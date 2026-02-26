from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

@dataclass(frozen=True)
class Room:
    id: int
    room_num: int
    category: int
    hotel_id: Optional[int]
    guest_session_id: Optional[int]
    id_minibar: int

@dataclass(frozen=True)
class Session:
    id: int
    room_id: int
    check_in: datetime
    check_out: Optional[datetime]
    transfer_id: Optional[int]

@dataclass(frozen=True)
class Product:
    id: int
    name: str
    price: Decimal

@dataclass(frozen=True)
class ItemCount:
    product_id: int
    name: str
    quantity: int
    unit_price: Optional[Decimal] = None

@dataclass(frozen=True)
class CheckoutReport:
    session_id: int
    room_id: int
    period_start: datetime
    period_end: datetime
    items: list[ItemCount]
    total: Decimal

@dataclass(frozen=True)
class RestockMissing:
    room_id: int
    items: list[ItemCount]

@dataclass(frozen=True)
class RestockResult:
    room_id: int
    transaction_id: int
    marked_at: datetime
