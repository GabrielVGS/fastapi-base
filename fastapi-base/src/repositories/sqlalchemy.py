import logging
from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import apaginate
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import select

from src.core.exceptions import ObjectNotFound, RepositoryError
from src.interfaces.repository import IRepository
from src.models.base import Base


ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
logger: logging.Logger = logging.getLogger(__name__)


class BaseSQLAlchemyRepository(IRepository, Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    A generic async SQLAlchemy repository base class that provides common CRUD operations.

    This class serves as a foundation for all repository classes, providing standardized
    methods for database operations while maintaining type safety through generics.

    Type Parameters:
        ModelType: The SQLAlchemy database model class (inherits from Base)
        CreateSchemaType: The Pydantic model for creating new objects
        UpdateSchemaType: The Pydantic model for updating existing objects
    """

    _model: Type[ModelType]

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the repository with a database session."""
        self.db = db

    async def create(self, obj_in: CreateSchemaType, **kwargs: Any) -> ModelType:
        """
        Create a new object in the database.

        Args:
            obj_in: The create schema containing the data for the new object
            **kwargs: Additional options:
                - add (bool): Whether to add the object to the session (default: True)
                - flush (bool): Whether to flush the session (default: True)
                - commit (bool): Whether to commit the transaction (default: True)
                - refresh (bool): Whether to refresh after commit (default: True)

        Returns:
            The created database object

        Raises:
            RepositoryError: If database operation fails
        """
        logger.info(f"Creating new {self._model.__name__} object")

        try:
            # Convert Pydantic model to SQLAlchemy model
            obj_data = obj_in.model_dump(exclude_unset=True)
            db_obj = self._model(**obj_data)

            add = kwargs.get("add", True)
            flush = kwargs.get("flush", True)
            commit = kwargs.get("commit", True)
            refresh = kwargs.get("refresh", True)

            if add:
                self.db.add(db_obj)

            if add and commit:
                await self.db.commit()
                if refresh:
                    await self.db.refresh(db_obj)
            elif add and flush:
                await self.db.flush()

            return db_obj

        except SQLAlchemyError as exc:
            logger.error(f"Failed to create {self._model.__name__}: {exc}")
            await self.db.rollback()
            raise RepositoryError(f"Failed to create object: {str(exc)}") from exc

    async def create_many(self, objects: List[CreateSchemaType]) -> List[ModelType]:
        """
        Create multiple objects in a single transaction.

        Args:
            objects: List of create schemas

        Returns:
            List of created database objects

        Raises:
            RepositoryError: If database operation fails
        """
        if not objects:
            return []

        logger.info(f"Creating {len(objects)} {self._model.__name__} objects")

        try:
            db_objects = [self._model(**obj.model_dump(exclude_unset=True)) for obj in objects]
            self.db.add_all(db_objects)
            await self.db.commit()

            # Refresh all objects
            for obj in db_objects:
                await self.db.refresh(obj)

            return db_objects

        except SQLAlchemyError as exc:
            logger.error(f"Failed to create multiple {self._model.__name__}: {exc}")
            await self.db.rollback()
            raise RepositoryError(f"Failed to create objects: {str(exc)}") from exc

    async def get(self, raise_if_not_found: bool = True, **kwargs: Any) -> Optional[ModelType]:
        """
        Get a single object by filter criteria.

        Args:
            raise_if_not_found: Whether to raise exception if object not found
            **kwargs: Filter criteria as key-value pairs

        Returns:
            The found object or None

        Raises:
            ObjectNotFound: If no object matches the criteria and raise_if_not_found is True
        """
        logger.debug(f"Fetching {self._model.__name__} by {kwargs}")

        try:
            query = select(self._model).filter_by(**kwargs)  # type: ignore
            result = await self.db.execute(query)
            obj = result.scalar_one_or_none()

            if not obj and raise_if_not_found:
                raise ObjectNotFound(f"{self._model.__name__} with {kwargs} not found")

            return obj

        except SQLAlchemyError as exc:
            logger.error(f"Failed to get {self._model.__name__}: {exc}")
            raise RepositoryError(f"Failed to get object: {str(exc)}") from exc

    async def get_with_relations(
        self, relations: List[str], raise_if_not_found: bool = True, **kwargs: Any
    ) -> Optional[ModelType]:
        """
        Get a single object with its relationships loaded.

        Args:
            relations: List of relationship names to load
            raise_if_not_found: Whether to raise exception if object not found
            **kwargs: Filter criteria as key-value pairs

        Returns:
            The found object with loaded relationships or None
        """
        logger.debug(f"Fetching {self._model.__name__} with relations {relations}")

        try:
            query = select(self._model).filter_by(**kwargs)  # type: ignore

            # Add selectinload for each relation
            for relation in relations:
                if hasattr(self._model, relation):
                    query = query.options(selectinload(getattr(self._model, relation)))

            result = await self.db.execute(query)
            obj = result.scalar_one_or_none()

            if not obj and raise_if_not_found:
                raise ObjectNotFound(f"{self._model.__name__} with {kwargs} not found")

            return obj

        except SQLAlchemyError as exc:
            logger.error(f"Failed to get {self._model.__name__} with relations: {exc}")
            raise RepositoryError(f"Failed to get object with relations: {str(exc)}") from exc

    async def update(self, obj_current: ModelType, obj_in: UpdateSchemaType) -> ModelType:
        """
        Update an existing object in the database.

        Args:
            obj_current: The current database object to update
            obj_in: The update schema containing the new data

        Returns:
            The updated database object

        Raises:
            RepositoryError: If database operation fails
        """
        logger.info(f"Updating {self._model.__name__} object")

        try:
            update_data = obj_in.model_dump(exclude_unset=True)

            for field, value in update_data.items():
                setattr(obj_current, field, value)

            self.db.add(obj_current)
            await self.db.commit()
            await self.db.refresh(obj_current)

            return obj_current

        except SQLAlchemyError as exc:
            logger.error(f"Failed to update {self._model.__name__}: {exc}")
            await self.db.rollback()
            raise RepositoryError(f"Failed to update object: {str(exc)}") from exc

    async def update_by_id(self, obj_id: Any, obj_in: UpdateSchemaType) -> ModelType:
        """
        Update an object by its ID.

        Args:
            obj_id: The ID of the object to update
            obj_in: The update schema containing the new data

        Returns:
            The updated database object

        Raises:
            ObjectNotFound: If no object with the given ID exists
        """
        obj = await self.get(id=obj_id)
        if obj is None:
            raise ObjectNotFound(f"{self._model.__name__} with id {obj_id} not found")
        return await self.update(obj, obj_in)

    async def delete(self, **kwargs: Any) -> None:
        """
        Delete an object from the database by filter criteria.

        Args:
            **kwargs: Filter criteria to identify the object to delete

        Raises:
            ObjectNotFound: If no object matches the criteria
            RepositoryError: If database operation fails
        """
        logger.info(f"Deleting {self._model.__name__} with {kwargs}")

        try:
            obj = await self.get(**kwargs)
            await self.db.delete(obj)
            await self.db.commit()

        except SQLAlchemyError as exc:
            logger.error(f"Failed to delete {self._model.__name__}: {exc}")
            await self.db.rollback()
            raise RepositoryError(f"Failed to delete object: {str(exc)}") from exc

    async def delete_by_id(self, obj_id: Any) -> None:
        """Delete an object by its ID."""
        await self.delete(id=obj_id)

    async def soft_delete(self, obj_id: Any, deleted_field: str = "deleted_at") -> ModelType:
        """
        Perform a soft delete by setting a boolean flag.

        Args:
            obj_id: The ID of the object to soft delete
            deleted_field: The name of the boolean field to set (default: 'deleted_at')

        Returns:
            The soft-deleted object
        """
        obj = await self.get(id=obj_id)
        if obj is None:
            raise ObjectNotFound(f"{self._model.__name__} with id {obj_id} not found")

        # set deleted_at to current timestamp
        if hasattr(obj, deleted_field):
            setattr(obj, deleted_field, datetime.now(timezone.utc))

        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)

        return obj

    async def exists(self, **kwargs: Any) -> bool:
        """
        Check if an object exists with the given criteria.

        Args:
            **kwargs: Filter criteria as key-value pairs

        Returns:
            True if object exists, False otherwise
        """
        obj = await self.get(raise_if_not_found=False, **kwargs)
        return obj is not None

    async def count(self, **kwargs: Any) -> int:
        """
        Count objects matching the given criteria.

        Args:
            **kwargs: Filter criteria as key-value pairs

        Returns:
            Number of matching objects
        """
        from sqlalchemy import func

        query = select(func.count(self._model.id)).filter_by(**kwargs)  # type: ignore
        result = await self.db.execute(query)
        return result.scalar() or 0

    def _get_order_by(
        self, sort_field: Optional[str] = None, sort_order: Optional[str] = None
    ) -> Any:
        """Get the order by clause for queries."""
        columns = self._model.__table__.columns

        if sort_field and sort_field not in columns:
            sort_field = "created_at" if hasattr(self._model, "created_at") else "id"

        if not sort_field:
            sort_field = "created_at" if "created_at" in columns else "id"

        if sort_order not in ["asc", "desc"]:
            sort_order = "desc"

        column = columns[sort_field]
        return column.asc() if sort_order == "asc" else column.desc()

    async def all(
        self,
        skip: int = 0,
        limit: int = 100,
        sort_field: Optional[str] = None,
        sort_order: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[ModelType]:
        """
        Get a list of all objects with optional pagination, sorting, and filtering.

        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            sort_field: Field name to sort by
            sort_order: Sort direction, 'asc' or 'desc'
            filters: Additional filter criteria

        Returns:
            List of database objects
        """
        try:
            order_by = self._get_order_by(sort_field, sort_order)
            query = select(self._model).offset(skip).limit(limit).order_by(order_by)  # type: ignore

            if filters:
                query = query.filter_by(**filters)  # type: ignore

            result = await self.db.execute(query)
            return result.scalars().all()

        except SQLAlchemyError as exc:
            logger.error(f"Failed to get all {self._model.__name__}: {exc}")
            raise RepositoryError(f"Failed to get objects: {str(exc)}") from exc

    async def paginate(
        self,
        sort_field: Optional[str] = None,
        sort_order: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Page[ModelType]:
        """
        Get paginated results using fastapi-pagination.

        Args:
            sort_field: Field name to sort by
            sort_order: Sort direction, 'asc' or 'desc'
            filters: Additional filter criteria

        Returns:
            Page object containing paginated results and metadata
        """
        try:
            order_by = self._get_order_by(sort_field, sort_order)
            query = select(self._model).order_by(order_by)  # type: ignore

            if filters:
                query = query.filter_by(**filters)  # type: ignore

            return await apaginate(self.db, query)

        except SQLAlchemyError as exc:
            logger.error(f"Failed to paginate {self._model.__name__}: {exc}")
            raise RepositoryError(f"Failed to paginate objects: {str(exc)}") from exc

    async def filter_by(
        self,
        filters: Dict[str, Any],
        sort_field: Optional[str] = None,
        sort_order: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[ModelType]:
        """
        Filter objects by multiple criteria with advanced filtering support.

        Args:
            filters: Dictionary of field: value pairs for filtering
            sort_field: Field name to sort by
            sort_order: Sort direction
            limit: Maximum number of results

        Returns:
            List of filtered objects
        """
        try:
            query = select(self._model)  # type: ignore

            # Apply filters
            for field, value in filters.items():
                if hasattr(self._model, field):
                    if isinstance(value, list):
                        # Handle IN clause
                        query = query.where(getattr(self._model, field).in_(value))
                    elif isinstance(value, dict) and "operator" in value:
                        # Handle complex operators
                        column = getattr(self._model, field)
                        operator = value["operator"]
                        val = value["value"]

                        if operator == "gt":
                            query = query.where(column > val)
                        elif operator == "gte":
                            query = query.where(column >= val)
                        elif operator == "lt":
                            query = query.where(column < val)
                        elif operator == "lte":
                            query = query.where(column <= val)
                        elif operator == "like":
                            query = query.where(column.like(f"%{val}%"))
                        elif operator == "ilike":
                            query = query.where(column.ilike(f"%{val}%"))
                    else:
                        # Simple equality
                        query = query.where(getattr(self._model, field) == value)

            # Apply sorting
            if sort_field or sort_order:
                order_by = self._get_order_by(sort_field, sort_order)
                query = query.order_by(order_by)

            # Apply limit
            if limit:
                query = query.limit(limit)

            result = await self.db.execute(query)
            return result.scalars().all()

        except SQLAlchemyError as exc:
            logger.error(f"Failed to filter {self._model.__name__}: {exc}")
            raise RepositoryError(f"Failed to filter objects: {str(exc)}") from exc

    async def get_or_create(
        self, obj_in: CreateSchemaType, defaults: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> tuple[ModelType, bool]:
        """
        Get an existing object or create it if it doesn't exist.

        Args:
            obj_in: The create schema for the new object
            defaults: Default values to use when creating (merged with obj_in)
            **kwargs: Filter criteria to search for existing object

        Returns:
            Tuple of (object, created) where created is True if object was created
        """
        try:
            existing_obj = await self.get(raise_if_not_found=False, **kwargs)

            if existing_obj:
                return existing_obj, False

            # Merge defaults if provided
            if defaults:
                create_data = obj_in.model_dump()
                create_data.update(defaults)
                obj_in = type(obj_in)(**create_data)

            new_obj = await self.create(obj_in)
            return new_obj, True

        except SQLAlchemyError as exc:
            logger.error(f"Failed get_or_create for {self._model.__name__}: {exc}")
            raise RepositoryError(f"Failed to get or create object: {str(exc)}") from exc

    # Alias for backward compatibility
    async def f(self, **kwargs: Any) -> List[ModelType]:
        """Find all objects matching the given filter criteria."""
        return await self.filter_by(kwargs)
