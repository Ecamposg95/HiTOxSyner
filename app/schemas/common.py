from dataclasses import dataclass
from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int


@dataclass
class Pagination:
    limit: int
    offset: int


def pagination_params(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)) -> Pagination:
    return Pagination(limit=limit, offset=offset)
