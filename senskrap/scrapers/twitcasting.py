from typing import Dict, List, Optional, Union
from requests import Session
from senskrap.base.base_scraper import BaseScraper
from datetime import datetime
from bs4 import BeautifulSoup


class TwitcastingScraper(BaseScraper):
    _BASE_URL = "https://twitcasting.tv/shop.php?date={}"

    def __init__(
        self,
        date: datetime,
        user_agent: Optional[Union[str, List[str]]] = None,
        session: Optional[Session] = None,
        proxies: Optional[Union[str, List[str], Dict[str, str]]] = None,
    ) -> None:
        super().__init__(
            self._BASE_URL.format(date.strftime("%Y%m%d")), user_agent, session, proxies
        )

    def scrape(self) -> None:
        """Fetches the HTML content and parses image URLs"""
        html = self.fetch_html()
        soup = BeautifulSoup(html, "html.parser")
        images = soup.find_all("img", class_="tw-shop-item-thumbnail-image")
        self.save_images(images)

    def save_images(self, images: list) -> None:
        """Extract and handle image URLs"""
        for image in images:
            src = image.get("src")
            if src:
                print(src)
