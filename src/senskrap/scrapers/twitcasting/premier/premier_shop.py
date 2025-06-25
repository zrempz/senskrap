from __future__ import annotations

from asyncio import Semaphore, gather
from typing import TYPE_CHECKING, Any

from aiohttp import ClientError

from .premier_parser import ItemParser, ListParser
from ..twitcasting_scraper import TwitcastingScraper

if TYPE_CHECKING:
    from datetime import datetime

    from aiohttp import ClientSession

    from .premier_genre import PremierGenre
    from .premier_item import PremierItem


class PremierScraper(TwitcastingScraper):
    """
    A scraper for fetching data about Premier broadcasts from Twitcasting.

    This class provides methods to search for broadcast URLs by various criteria
    and to scrape detailed information from those URLs.
    """

    def __init__(
        self,
        user_agent: str | list[str] | None = None,
        session: ClientSession | None = None,
        proxies: str | list[str] | None = None,
        headers: dict[str, str] | None = None,
        timeout: int = 10,
    ) -> None:
        """
        Initializes the PremierScraper.

        Args:
            user_agent: The User-Agent string or a list of strings to rotate through.
            session: An optional aiohttp.ClientSession to use for requests.
            proxies: An optional proxy URL or a list of URLs to rotate through.
            headers: Optional dictionary of headers to include in every request.
            timeout: The default timeout in seconds for requests.
        """
        super().__init__(
            endpoint="shop.php",
            user_agent=user_agent,
            session=session,
            proxies=proxies,
            headers=headers,
            timeout=timeout,
        )
        self.list_parser = ListParser()
        self.item_parser = ItemParser()

    async def scrape(
        self,
        *,
        search: str | None = None,
        date: datetime | None = None,
        genre: PremierGenre | None = None,
        max_pages: int | None = None,
        concurrency: int = 10,
        strip: bool = False,
    ) -> list[dict]:
        """
        A generic scraper that gets full item data based on a single search criterion.

        This is the primary method for getting detailed data. It first finds all
        relevant URLs and then concurrently scrapes each one.

        Args:
            search: The search term to query.
            date: The specific date to query.
            genre: The specific genre to query.
            max_pages: The maximum number of result pages to process.
            concurrency: The number of concurrent requests for scraping details.
            strip: If True, strips extra whitespace from string fields in the result.

        Returns:
            A list of dictionaries, where each dictionary represents a scraped item.

        Raises:
            ValueError: If more than one or zero search criteria are provided.
        """
        urls = await self.search(
            search=search,
            date=date,
            genre=genre,
            max_pages=max_pages,
            concurrency=concurrency,
        )
        return await self._scrape_items_from_urls(urls, concurrency, strip=strip)

    async def search(
        self,
        *,
        search: str | None = None,
        date: datetime | None = None,
        genre: PremierGenre | None = None,
        max_pages: int | None = None,
        concurrency: int = 10,
    ) -> list[str]:
        """
        A generic search that gets item URLs based on a single search criterion.

        This method is for discovering URLs without fetching their full details.

        Args:
            search: The search term to query.
            date: The specific date to query.
            genre: The specific genre to query.
            max_pages: The maximum number of result pages to process.
            concurrency: The number of concurrent requests for fetching result pages.

        Returns:
            A list of URLs matching the search criterion.

        Raises:
            ValueError: If more than one or zero search criteria are provided.
        """
        payload = {}
        criteria = [c for c in (search, date, genre) if c is not None]
        if len(criteria) != 1:
            msg = "Exactly one search criterion (search, date, or genre) must be provided."
            raise ValueError(msg)

        if search is not None:
            payload = {"search": search}
        elif date is not None:
            payload = {"date": date.strftime("%Y%m%d")}
        elif genre is not None:
            payload = {"genre": str(genre.value)}

        return await self._scrape_urls(payload, max_pages, concurrency)

    async def get_item_info(self, url: str, *, strip: bool = False) -> dict | None:
        """
        Fetches a single item's page and returns its data as a dictionary.

        Args:
            url: The full URL of the item page to scrape.
            strip: If True, strips extra whitespace from string fields in the result.

        Returns:
            A dictionary containing the scraped item data, or None if scraping fails.
        """
        item = await self._get_premier_item(url=url, strip=strip)
        return item.to_dict() if item else None

    async def scrape_by_term(self, search: str, **kwargs) -> list[dict]:
        """Convenience wrapper to scrape all items by a search term."""
        return await self.scrape(search=search, **kwargs)

    async def scrape_by_date(self, date: datetime, **kwargs) -> list[dict]:
        """Convenience wrapper to scrape all items by a specific date."""
        return await self.scrape(date=date, **kwargs)

    async def scrape_by_genre(self, genre: PremierGenre, **kwargs) -> list[dict]:
        """Convenience wrapper to scrape all items by a specific genre."""
        return await self.scrape(genre=genre, **kwargs)

    async def search_by_term(self, search: str, **kwargs) -> list[str]:
        """Convenience wrapper to find all item URLs by a search term."""
        return await self.search(search=search, **kwargs)

    async def search_by_date(self, date: datetime, **kwargs) -> list[str]:
        """Convenience wrapper to find all item URLs by a specific date."""
        return await self.search(date=date, **kwargs)

    async def search_by_genre(self, genre: PremierGenre, **kwargs) -> list[str]:
        """Convenience wrapper to find all item URLs by a specific genre."""
        return await self.search(genre=genre, **kwargs)

    async def _get_premier_item(
        self, url: str, *, strip: bool = False
    ) -> PremierItem | None:
        """Fetches and parses a single item page, returning a PremierItem object."""
        try:
            html = await self.fetch(url=url)
            if not html:
                return None
            return self.item_parser.parse(html, url=url, strip=strip)
        except (ClientError, TypeError, TimeoutError):
            return None

    async def _scrape_urls(
        self, payload: dict[str, Any], max_pages: int | None, concurrency: int
    ) -> list[str]:
        """Fetches all item URLs from paginated search results."""
        try:
            initial_html = await self.fetch_html(params=payload)
            if not initial_html:
                return []
        except (ClientError, TypeError, TimeoutError):
            return []

        all_links, actual_total_pages = self.list_parser.parse(initial_html)

        pages_to_scrape = (
            min(actual_total_pages, max_pages)
            if max_pages is not None
            else actual_total_pages
        )

        if pages_to_scrape <= 1:
            return all_links

        semaphore = Semaphore(concurrency)
        tasks = [
            self._fetch_page_links(page_num, payload, semaphore)
            for page_num in range(1, pages_to_scrape)
        ]
        results_from_other_pages = await gather(*tasks)

        for page_links in results_from_other_pages:
            all_links.extend(page_links)

        return all_links

    async def _fetch_page_links(
        self, page_num: int, payload: dict[str, Any], semaphore: Semaphore
    ) -> list[str]:
        """Fetches and parses a single page of search results for item URLs."""
        async with semaphore:
            try:
                html = await self.fetch_html(params={**payload, "p": page_num})
                links, _ = self.list_parser.parse(html)
            except (ClientError, TypeError, TimeoutError):
                return []
            else:
                return links

    async def _scrape_items_from_urls(
        self, urls: list[str], concurrency: int, *, strip: bool = False
    ) -> list[dict]:
        """Concurrently scrapes item details from a list of URLs."""
        if not urls:
            return []

        semaphore = Semaphore(concurrency)

        tasks = [self.get_item_info(url, strip=strip) for url in urls]

        async def run_with_semaphore(task):
            async with semaphore:
                return await task

        results = await gather(*(run_with_semaphore(task) for task in tasks))

        return [item for item in results if item is not None]
