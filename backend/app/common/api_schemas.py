from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ApiError(ApiModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ApiResponse[DataT](ApiModel):
    success: bool = True
    data: DataT | None = None
    error: ApiError | None = None


class Pagination(ApiModel):
    page: int
    limit: int
    total_items: int
    total_pages: int


class PaginatedData[DataT](ApiModel):
    items: list[DataT]
    pagination: Pagination
