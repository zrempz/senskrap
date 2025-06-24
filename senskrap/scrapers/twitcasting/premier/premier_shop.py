from asyncio import Semaphore, gather
from typing import Any, Dict, List, Optional, Union
from aiohttp import ClientSession
from datetime import datetime

from .premier_parser import ItemParser, ListParser
from ..twitcasting_scraper import TwitcastingScraper


class PremierScraper(TwitcastingScraper):
    def __init__(
        self,
        user_agent: Optional[Union[str, List[str]]] = None,
        session: Optional[ClientSession] = None,
        proxies: Optional[Union[str, List[str]]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 10,
    ) -> None:
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

    async def scrape(self, *args: Any, **kwargs: Any) -> Any:
        pass

    async def scrape_urls(
        self,
        payload: Dict[str, Any],
        max_pages: Optional[int] = None,
        concurrency: int = 10,
    ) -> List[str]:
        try:
            initial_html = await self.fetch_html(params=payload)
            if not initial_html:
                return []
        except Exception as e:
            print(f"CRITICAL: Failed to get initial page for {payload}. Error: {e}")
            return []

        all_links, actual_total_pages = self.list_parser.parse(initial_html)

        pages_to_scrape = actual_total_pages
        if max_pages is not None:
            pages_to_scrape = min(actual_total_pages, max_pages)

        if pages_to_scrape <= 1:
            return all_links

        semaphore = Semaphore(concurrency)
        tasks = []

        async def fetch_page_links(page_num: int) -> List[str]:
            async with semaphore:
                try:
                    html = await self.fetch_html(params={**payload, "p": page_num})
                    links, _ = self.list_parser.parse(html)
                    return links
                except Exception as e:
                    print(
                        f"Error getting links from page {page_num} with params {payload}: {e}"
                    )
                    return []

        for page_num in range(1, pages_to_scrape):
            tasks.append(fetch_page_links(page_num))

        results_from_other_pages = await gather(*tasks)
        for page_links in results_from_other_pages:
            all_links.extend(page_links)

        return all_links

    async def search_by_term(
        self,
        search: str,
        max_pages: Optional[int] = None,
        concurrency: int = 10,
    ) -> List[str]:
        """Wrapper to search by term with pagination control."""
        payload = {"search": search}
        return await self.scrape_urls(
            payload, max_pages=max_pages, concurrency=concurrency
        )

    async def search_by_date(
        self,
        date: datetime,
        max_pages: Optional[int] = None,
        concurrency: int = 10,
    ) -> List[str]:
        """Wrapper to search by date with pagination control."""
        payload = {"date": date.strftime("%Y%m%d")}
        return await self.scrape_urls(
            payload, max_pages=max_pages, concurrency=concurrency
        )

    async def get_item_details(self, url: str, strip: bool = False) -> Optional[dict]:
        try:
            html = await self.fetch(url=url)
            if not html:
                return None
            return self.item_parser.parse(html, url=url, strip=strip).to_dict()
        except Exception as e:
            print(f"Error getting information from {url}: {e}")
            return None
