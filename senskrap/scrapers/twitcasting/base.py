from typing import Dict, List, Optional, Union
from senskrap.base import BaseScraper
from aiohttp import ClientSession


class TwitcastingBase(BaseScraper):
    _BASE_URL = "https://twitcasting.tv"

    def __init__(
        self,
        endpoint: str,
        user_agent: Optional[Union[str, List[str]]] = None,
        session: Optional[ClientSession] = None,
        proxies: Optional[Union[str, List[str]]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 10,
    ) -> None:
        super().__init__(
            url=f"{self._BASE_URL}/{endpoint}",
            user_agent=user_agent,
            session=session,
            proxies=proxies,
            headers=headers,
            timeout=timeout,
        )
