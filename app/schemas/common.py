from dataclasses import dataclass
from typing import Generic, TypeVar

from fastapi import HTTPException, Query
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


def updates(data: BaseModel, nullable: set[str] | frozenset[str] = frozenset()) -> dict:
    """Campos enviados en un PATCH; un null explícito en un campo no nullable responde 422."""
    payload = data.model_dump(exclude_unset=True)
    invalid = [field for field, value in payload.items() if value is None and field not in nullable]
    if invalid:
        raise HTTPException(status_code=422, detail=f"Estos campos no admiten null: {', '.join(invalid)}")
    return payload
