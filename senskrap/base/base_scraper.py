from types import TracebackType
from aiohttp import ClientSession, ClientTimeout
from aiohttp_socks import ProxyConnector
from abc import ABC, abstractmethod
from random import choice
from typing import Any, Dict, Optional, Self, Type, Union, List

from bs4 import Tag


class BaseScraper(ABC):
    """Abstract base class for web scraping implementations.

    Provides core functionality for HTTP requests with:
    - Configurable user agents
    - Proxy support (HTTP/SOCKS)
    - Custom headers
    - Retry mechanism
    - Async context management
    """

    _DEFAULT_USER_AGENTS = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.61 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.62 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.63 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.64 Safari/537.36",
    )

    def __init__(
        self,
        url: str,
        user_agent: Optional[Union[str, List[str], bool]] = None,
        session: Optional[ClientSession] = None,
        proxies: Optional[Union[str, List[str]]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 10,
    ) -> None:
        """Initialize web scraper instance.

        Args:
            url: Target URL to scrape
            user_agent: Custom user agent(s). String or list for random selection
            session: Existing aiohttp session to reuse
            proxies: Proxy URL(s) for connections
            headers: Additional HTTP headers
            timeout: Request timeout in seconds
        """
        self.url = url
        self._session = session
        self._external_session = session is not None
        self._internal_session: Optional[ClientSession] = None
        self._headers = (
            self._build_headers(user_agent, headers)
            if not self._external_session
            else None
        )
        self._proxy_url = self._resolve_proxy_url(proxies)
        self._closed = False
        self.timeout = timeout

    def _build_headers(
        self,
        user_agent: Optional[Union[str, List[str], bool]],
        headers: Optional[Dict[str, str]],
    ) -> Dict[str, str]:
        """Merge base headers with custom headers and resolved User-Agent.

        Returns:
            Final headers dictionary for requests
        """
        if not headers:
            return {"User-Agent": self._resolve_user_agent(user_agent)}

        if user_agent:
            return {**headers, "User-Agent": self._resolve_user_agent(user_agent)}

        return headers

    def _resolve_user_agent(
        self, user_agent: Optional[Union[str, List[str], bool]]
    ) -> str:
        """Select User-Agent string from available options.

        Returns:
            Single User-Agent string
        """
        if isinstance(user_agent, str):
            return user_agent
        if isinstance(user_agent, list) and user_agent:
            return choice(user_agent)
        return choice(self._DEFAULT_USER_AGENTS)

    def _resolve_proxy_url(
        self, proxies: Optional[Union[str, List[str]]]
    ) -> Optional[str]:
        """Select proxy URL from provided options.

        Returns:
            Single proxy URL or None
        """
        if not proxies:
            return None
        if isinstance(proxies, str):
            return proxies
        if isinstance(proxies, list):
            return choice(proxies)

    def _create_connector(self) -> Optional[ProxyConnector]:
        """Create proxy connector if proxy URL is valid."""
        if not self._proxy_url:
            return None
        try:
            return ProxyConnector.from_url(self._proxy_url)
        except ValueError:
            return None

    @property
    def session(self) -> ClientSession:
        """Lazy-loaded aiohttp session with proxy support."""
        if self._session is not None:
            return self._session

        if self._internal_session is None:
            connector = self._create_connector()
            self._internal_session = ClientSession(
                headers=self._headers,
                connector=connector,
            )

        return self._internal_session

    @abstractmethod
    async def scrape(self, **kwargs: Any) -> Any:
        """Implement scraping logic in derived classes.

        Returns:
            bool: Scraping success status
        """
        pass

    async def fetch(
        self,
        url: Optional[str] = None,
        method: str = "GET",
        timeout: Optional[int] = None,
        allow_redirects: bool = True,
        **kwargs: Any,
    ) -> str:
        """Fetch content from any URL with configurable parameters.

        Args:
            url: Target URL to request
            method: HTTP method (GET, POST, etc.)
            timeout: Custom timeout in seconds (overrides class timeout)
            **kwargs: Additional arguments for aiohttp request

        Returns:
            Response content as string

        Raises:
            ConnectionError: On network or HTTP errors
        """
        try:
            async with self.session.request(
                method,
                url or self.url,
                timeout=ClientTimeout(total=timeout or self.timeout),
                allow_redirects=allow_redirects,
                **kwargs,
            ) as response:
                response.raise_for_status()
                return await response.text()
        except Exception as e:
            if hasattr(e, "status"):
                raise ConnectionError(f"HTTP error {e} for URL: {url}") from e
            raise ConnectionError(
                f"Network error occurred: {str(e)} for URL: {url}"
            ) from e

    async def fetch_html(self, **kwargs) -> str:
        """Alias for fetch() with HTML-specific naming."""
        return await self.fetch(**kwargs)

    def _extract_text(self, element: Optional[Tag], strip: bool = True) -> Optional[str]:
        """Safely extract and strip text from a BeautifulSoup element."""
        return element.get_text(strip=strip) if element else None

    def _extract_with_line_breaks(
        self, element: Optional[Tag], strip: bool = True
    ) -> Optional[str]:
        """
        Extracts text, using newlines as separators for tags like <br>.
        This is the recommended, non-destructive method.
        """
        return element.get_text(separator="\n", strip=strip) if element else None

    async def close(self) -> None:
        """Clean up internal resources."""
        if self._closed:
            return

        self._closed = True
        if not self._external_session and self._internal_session:
            await self._internal_session.close()
            self._internal_session = None

    async def __aenter__(self) -> Self:
        """Async context manager entry point."""
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Async context manager exit point.

        Ensures proper resource cleanup.
        """
        await self.close()
