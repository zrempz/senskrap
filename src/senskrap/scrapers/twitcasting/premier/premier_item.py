from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class PremierTicket:
    title: str | None
    price: str | None


@dataclass
class PremierItem:
    url: str
    title: str | None
    author: str | None
    author_url: str | None
    date: str | None
    description: str | None
    image_url: str | None
    available_until: str | None
    archive_sales_deadline: str | None
    tickets: list[PremierTicket] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)
