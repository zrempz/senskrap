from __future__ import annotations

from abc import abstractmethod
from copy import copy
from typing import Any
from urllib.parse import urljoin

from bs4 import Tag
from bs4.element import NavigableString


class BaseParser:
    """Base class for parsers with utility methods."""

    @staticmethod
    def extract_text(element: Tag | None, *, strip: bool = True) -> str | None:
        """
        Safely extracts text from a BeautifulSoup tag.

        Args:
            element (Optional[Tag]): The BeautifulSoup element to extract from.
            strip (bool): Whether to strip leading/trailing whitespace. Defaults to True.

        Returns:
            Optional[str]: The extracted text, or None if the element is None.
        """
        return element.get_text(strip=strip) if element else None

    @staticmethod
    def extract_with_line_breaks(element: Tag | None, *, strip: bool = False) -> str | None:
        """
        Extracts readable text from a BeautifulSoup tag, mimicking page formatting
        with line breaks after block elements like <p>, <br>, <div>, etc.

        This version is highly optimized for performance and correctness.

        Args:
            element (Optional[Tag]): The BeautifulSoup element from which to extract text.
            strip (bool): If True, strips leading/trailing whitespace from each line.

        Returns:
            Optional[str]: Clean, readable text, or None if the element is None.
        """
        if not element:
            return None
        element_copy = copy(element)

        br_tags: set[str] = {"br"}
        block_tags: set[str] = {
            "p",
            "div",
            "li",
            "h1",
            "h2",
            "h3",
            "section",
            "article",
            "br",
        }

        for tag in element_copy.find_all(br_tags.union(block_tags)):
            if isinstance(tag, Tag):
                if tag.name in br_tags:
                    tag.replace_with(NavigableString("\n"))
                else:
                    tag.insert_after(NavigableString("\n"))

        text = element_copy.get_text()

        if strip:
            lines = (line.strip() for line in text.splitlines())
            return "\n".join(line for line in lines if line)
        return text.strip()

    @staticmethod
    def extract_urls(elements: list[Tag], attr: str = "href", base_url: str | None = None) -> list[str]:
        """
        Extract URLs from elements by specified attribute, resolving relative URLs if base_url provided.

        Args:
            elements: List of HTML elements.
            attr: Attribute name to extract URL from (e.g., 'href', 'src').
            base_url: Base URL for resolving relative URLs.

        Returns:
            List of URLs as strings.
        """
        return [url for el in elements if (url := BaseParser.extract_url(el, attr=attr, base_url=base_url))]

    @staticmethod
    def extract_url(element: Tag, attr: str = "href", base_url: str | None = None) -> str | None:
        """
        Extracts a single URL from an element.

        Args:
            element: The HTML element.
            attr: The attribute to extract the URL from.
            base_url: The base URL for resolving relative paths.

        Returns:
            The full URL as a string, or None.
        """
        url = element.get(attr)
        if not url:
            return None
        return urljoin(base_url, str(url)) if base_url else str(url)

    @abstractmethod
    def parse(self, *args: Any, **kwargs: Any) -> Any:
        """
        Abstract method that must be implemented by subclasses.

        Parses the input and returns parsed data.

        Args:
            *args: Positional arguments for the parser.
            **kwargs: Keyword arguments for the parser.

        Returns:
            Any: The result of the parsing operation.
        """
