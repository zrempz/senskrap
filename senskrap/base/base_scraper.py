from abc import ABC, abstractmethod
from random import choice
from requests import Session
from typing import Dict, Optional, Union, List


class BaseScraper(ABC):
    _DEFAULT_USER_AGENTS = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    )
    _BASE_HEADERS = {
        "Accept-Language": "en-US,en;q=0.8",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    def __init__(
        self,
        url: str,
        user_agent: Optional[Union[str, List[str]]] = None,
        session: Optional[Session] = None,
        proxies: Optional[Union[str, List[str], Dict[str, str]]] = None,
    ) -> None:
        self.url = url
        self.session = session or Session()
        self._external_session = session is not None
        self.session.headers.update(self._BASE_HEADERS)
        self.session.headers.update(
            {"User-Agent": self._resolve_user_agent(user_agent)}
        )
        normalized_proxies = self._normalize_proxies(proxies)
        if normalized_proxies:
            self.session.proxies.update(normalized_proxies)

    def _resolve_user_agent(self, user_agent: Optional[Union[str, List[str]]]) -> str:
        """Return a single user-agent string, randomly selected if a list is given"""
        if isinstance(user_agent, str):
            return user_agent
        if isinstance(user_agent, list) and user_agent:
            return choice(user_agent)
        return choice(self._DEFAULT_USER_AGENTS)

    def _normalize_proxies(
        self, proxies: Optional[Union[str, List[str], Dict[str, str]]]
    ) -> Optional[Dict[str, str]]:
        """Standardize proxy input into a dictionary form"""
        if not proxies:
            return None
        if isinstance(proxies, dict):
            return proxies
        if isinstance(proxies, str):
            return {"http": proxies, "https": proxies}
        if isinstance(proxies, list) and proxies:
            proxy = choice(proxies)
            return {"http": proxy, "https": proxy}
        return None

    @abstractmethod
    def scrape(self) -> None:
        """Abstract method to implement scraping logic in derived classes"""
        pass

    def fetch_html(self, timeout: int = 10) -> str:
        """Perform a simple GET request and return HTML content"""
        response = self.session.get(self.url, timeout=timeout)
        response.raise_for_status()
        return response.text

    def close(self) -> None:
        """Gracefully close the session if it was created internally"""
        if not self._external_session:
            self.session.close()

    def __enter__(self):
        """Support for context manager entry"""
        return self

    def __exit__(self):
        """Support for context manager exit; ensures session closure"""
        self.close()
