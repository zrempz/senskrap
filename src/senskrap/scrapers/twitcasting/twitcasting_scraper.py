from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urljoin

from senskrap.base import BaseScraper

if TYPE_CHECKING:
    from aiohttp import ClientSession


class TwitcastingScraper(BaseScraper):
    _BASE_URL = "https://twitcasting.tv"

    def __init__(
        self,
        endpoint: str,
        user_agent: str | list[str] | None = None,
        session: ClientSession | None = None,
        proxies: str | list[str] | None = None,
        headers: dict[str, str] | None = None,
        timeout: int = 10,
    ) -> None:
        super().__init__(
            url=urljoin(self._BASE_URL, endpoint),
            user_agent=user_agent,
            session=session,
            proxies=proxies,
            headers=headers,
            timeout=timeout,
        )
