from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass
class PremierTicket:
    title: Optional[str]
    price: Optional[str]


@dataclass
class PremierItem:
    url: str
    title: Optional[str]
    author: Optional[str]
    author_url: Optional[str]
    date: Optional[str]
    description: Optional[str]
    image_url: Optional[str]
    available_until: Optional[str]
    archive_sales_deadline: Optional[str]
    tickets: List[PremierTicket] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)
