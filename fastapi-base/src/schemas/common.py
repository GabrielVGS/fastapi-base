from typing import Any, Dict, Generic, Optional, TypeVar

from pydantic import BaseModel


T = TypeVar("T")


class IResponseBase(BaseModel, Generic[T]):  # type: ignore
    message: str = ""
    meta: Optional[Dict[str, Any]] = {}
    data: Optional[T] = None
    status: bool = True


class IGetResponseBase(IResponseBase[T], Generic[T]):
    message: str = "Data fetched correctly"
    data: Optional[T] = None


class IPostResponseBase(IResponseBase[T], Generic[T]):
    message: str = "Data created correctly"
