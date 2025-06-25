from __future__ import annotations

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .premier_item import (
    PremierItem,
    PremierTicket,
)
from ..twitcasting_parser import TwitcastingParser


class ListParser(TwitcastingParser):
    _THUMBNAIL_LIST_SELECTOR = "a.tw-shop-item-thumbnail"
    _PAGER_LAST_PAGE_SELECTOR = "div.tw-pager a:last-of-type"
    _BASE_URL = "https://twitcasting.tv"

    def parse(self, html: str) -> tuple[list[str], int]:
        soup = BeautifulSoup(html, "lxml")
        if soup.select_one(self._EMPTY_STATE_SELECTOR):
            return [], 0

        links = self.extract_urls(soup.select(self._THUMBNAIL_LIST_SELECTOR), base_url=self._BASE_URL)
        total_pages = self._get_total_pages(soup)

        return links, total_pages

    def _get_total_pages(self, soup: BeautifulSoup) -> int:
        last_page_element = soup.select_one(self._PAGER_LAST_PAGE_SELECTOR)
        if not last_page_element:
            return 1
        try:
            return int(last_page_element.get_text(strip=True))
        except (ValueError, TypeError):
            return 1


class ItemParser(TwitcastingParser):
    _TITLE_SELECTOR = "h2.tw-shop-item-header-title"
    _DATE_SELECTOR = "time.tw-shop-item-header-date"
    _DESCRIPTION_SELECTOR = "p.tw-shop-item-description"
    _AVAILABLE_UNTIL_SELECTOR = "time.tw-shop-item-header-expire-date"
    _IMAGE_SELECTOR = "img.tw-shop-item-cover-image"
    _ARCHIVE_DEADLINE_SELECTOR = "span.tw-shop-item-header-archieve-expire-date"
    _AUTHOR_SELECTOR = "span.tw-shop-item-header-user-name"
    _AUTHOR_URL_SELECTOR = "a.tw-shop-item-header-user"
    _TICKET_CONTAINER_SELECTOR = ".tw-shop-ticket-button2"
    _TICKET_TITLE_SELECTOR = ".tw-shop-ticket-button2-title"
    _TICKET_PRICE_SELECTOR = ".tw-shop-ticket-button2-price"
    _BASE_URL = "https://twitcasting.tv"

    def parse(self, html: str, url: str, *, strip: bool = False) -> PremierItem:
        """Parses the item detail HTML into a TwitcastingItem object."""
        soup = BeautifulSoup(html, "lxml")

        image_element = soup.select_one(self._IMAGE_SELECTOR)
        url_author_elem = soup.select_one(self._AUTHOR_URL_SELECTOR)
        available_until_raw = self.extract_text(soup.select_one(self._AVAILABLE_UNTIL_SELECTOR))
        archive_sales_raw = self.extract_text(soup.select_one(self._ARCHIVE_DEADLINE_SELECTOR))
        tickets = []
        for container in soup.select(self._TICKET_CONTAINER_SELECTOR):
            ticket_title = self.extract_text(container.select_one(self._TICKET_TITLE_SELECTOR))
            ticket_price_raw = self.extract_text(container.select_one(self._TICKET_PRICE_SELECTOR))
            ticket_price = ticket_price_raw.replace("(tax included)", "").strip() if ticket_price_raw else None
            tickets.append(PremierTicket(title=ticket_title, price=ticket_price))

        return PremierItem(
            url=url,
            title=self.extract_text(soup.select_one(self._TITLE_SELECTOR)),
            author=self.extract_text(soup.select_one(self._AUTHOR_SELECTOR)),
            author_url=(urljoin(self._BASE_URL, str(url_author_elem.get("href", ""))) if url_author_elem else None),
            date=self.extract_text(soup.select_one(self._DATE_SELECTOR)),
            description=self.extract_with_line_breaks(soup.select_one(self._DESCRIPTION_SELECTOR), strip=strip),
            image_url=(urljoin(self._BASE_URL, str(image_element.get("src", ""))) if image_element else None),
            available_until=(
                available_until_raw.replace("Available Period", "").strip() if available_until_raw else None
            ),
            archive_sales_deadline=(
                archive_sales_raw.replace("Archive sales deadline:", "").strip() if archive_sales_raw else None
            ),
            tickets=tickets,
        )
