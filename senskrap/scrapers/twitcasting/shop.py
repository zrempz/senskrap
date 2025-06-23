from datetime import datetime
from typing import Any, List, Optional, Union, Dict
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from .base import TwitcastingBase
from urllib.parse import urljoin


class TwitcastingShop(TwitcastingBase):
    _THUMBNAIL_LIST_SELECTOR = "a.tw-shop-item-thumbnail"
    _TITLE_SELECTOR = "h2.tw-shop-item-header-title"
    _DATE_SELECTOR = "time.tw-shop-item-header-date"
    _DESCRIPTION_SELECTOR = "p.tw-shop-item-description"
    _AVAILABLE_UNTIL_SELECTOR = "time.tw-shop-item-header-expire-date"
    _IMAGE_SELECTOR = "img.tw-shop-item-cover-image"
    _ARCHIVE_DEADLINE_SELECTOR = "span.tw-shop-item-header-archieve-expire-date"
    _AUTHOR_SELECTOR = "span.tw-shop-item-header-user-name"
    _ACTOR_URL_SELECTOR = "a.tw-shop-item-header-user"
    _TICKET_CONTAINER_SELECTOR = ".tw-shop-ticket-button2"
    _TICKET_TITLE_SELECTOR = ".tw-shop-ticket-button2-title"
    _TICKET_PRICE_SELECTOR = ".tw-shop-ticket-button2-price"

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

    async def scrape(self, **kwargs: Any) -> Any:
        pass

    async def scrape_by_date(self, date: datetime) -> List[str]:
        try:
            payload = {"date": date.strftime("%Y%m%d")}
            html = await self.fetch_html(params=payload)
        except Exception as e:
            print(f"Error fetching HTML for date {date.strftime('%Y-%m-%d')}: {e}")
            return []

        soup = BeautifulSoup(html, "lxml")
        atags = soup.select(self._THUMBNAIL_LIST_SELECTOR)

        if not atags:
            print("No thumbnail links found.")
            return []

        return self.get_links(atags)

    def get_links(self, atags: list) -> list[str]:
        return [urljoin(self._BASE_URL, a.get("href", "")) for a in atags]

    async def get_info(self, url: str, strip: bool = True) -> dict:
        try:
            html = await self.fetch(url=url)
            if not html:
                return {}
        except Exception as e:
            print(f"Error fetching item info from {url}: {e}")
            return {}

        soup = BeautifulSoup(html, "lxml")

        title = self._extract_text(soup.select_one(self._TITLE_SELECTOR), strip=strip)
        date = self._extract_text(soup.select_one(self._DATE_SELECTOR, strip=strip))
        description = self._extract_with_line_breaks(
            soup.select_one(self._DESCRIPTION_SELECTOR), strip=strip
        )
        available_until = self._extract_text(
            soup.select_one(self._AVAILABLE_UNTIL_SELECTOR), strip=strip
        )

        image_element = soup.select_one(self._IMAGE_SELECTOR)

        image_url = urljoin(
            self._BASE_URL, str(image_element.get("src") if image_element else None)
        )

        archive_sales_deadline = self._extract_text(
            soup.select_one(self._ARCHIVE_DEADLINE_SELECTOR), strip=strip
        )
        author = self._extract_text(soup.select_one(self._AUTHOR_SELECTOR), strip=strip)

        url_actor_elem = soup.select_one(self._ACTOR_URL_SELECTOR)
        url_actor = (
            f"{self._BASE_URL}{url_actor_elem.get('href')}"
            if url_actor_elem and url_actor_elem.has_attr("href")
            else None
        )

        ticket_container = soup.select_one(self._TICKET_CONTAINER_SELECTOR)
        ticket_title = (
            self._extract_text(
                ticket_container.select_one(self._TICKET_TITLE_SELECTOR), strip=strip
            )
            if ticket_container
            else None
        )
        ticket_price_elem = (
            ticket_container.select_one(self._TICKET_PRICE_SELECTOR)
            if ticket_container
            else None
        )
        ticket_price_raw = (
            self._extract_text(ticket_price_elem, strip=strip)
            if ticket_price_elem
            else None
        )
        ticket_price = (
            ticket_price_raw.replace("(tax included)", "").strip()
            if ticket_price_raw
            else None
        )

        return {
            "title": title,
            "author": author,
            "actor_url": url_actor,
            "date": date,
            "description": description,
            "image_url": image_url,
            "available_until": available_until,
            "archive_sales_deadline": archive_sales_deadline,
            "ticket_title": ticket_title,
            "ticket_price": ticket_price,
            "url": url,
        }
