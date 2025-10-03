import logging
from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, Type

from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import apaginate
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from src.core.exceptions import ObjectNotFound, RepositoryError
from src.interfaces.repository import IRepository
from src.repositories.results import TimeBasedPaginationResult
from src.repositories.types import CreateSchemaType, ModelType, UpdateSchemaType


logger: logging.Logger = logging.getLogger(__name__)


class BaseSQLAlchemyRepository(IRepository, Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    A generic async SQLAlchemy repository base class that provides common CRUD operations.

    This class serves as a foundation for all repository classes, providing standardized
    methods for database operations while maintaining type safety through generics.

    Type Parameters:
        ModelType: The SQLModel database model class
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
            db_obj = self._model.model_validate(obj_in)

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
            return []  # pragma: no cover

        logger.info(f"Creating {len(objects)} {self._model.__name__} objects")

        try:
            db_objects = [self._model.model_validate(obj) for obj in objects]
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

    async def paginate_by_time(
        self,
        cursor: Optional[datetime] = None,
        limit: int = 20,
        direction: str = "next",
        time_field: str = "created_at",
        sort_order: str = "desc",
        filters: Optional[Dict[str, Any]] = None,
        include_total_count: bool = False,
    ) -> TimeBasedPaginationResult[ModelType]:
        """
        Paginate results using time-based (cursor) pagination.

        Args:
            cursor: The timestamp cursor to start from
            limit: Maximum number of items to return
            direction: Pagination direction ("next" or "previous")
            time_field: The timestamp field to use for pagination (default: "created_at")
            sort_order: Sort order ("desc" or "asc")
            filters: Additional filter criteria
            include_total_count: Whether to include total count (expensive)

        Returns:
            TimeBasedPaginationResult containing items and pagination metadata

        Raises:
            RepositoryError: If the time field doesn't exist or query fails
        """
        try:
            # Validate time field exists
            if not hasattr(self._model, time_field):
                raise RepositoryError(
                    f"Time field '{time_field}' does not exist on {self._model.__name__}"
                )

            time_column = getattr(self._model, time_field)

            # Build base query
            query = select(self._model)  # type: ignore

            # Apply filters if provided
            if filters:
                query = query.filter_by(**filters)  # type: ignore

            # Apply cursor-based filtering
            if cursor:
                if direction == "next":
                    if sort_order == "desc":
                        query = query.where(time_column < cursor)
                    else:
                        query = query.where(time_column > cursor)
                else:  # previous
                    if sort_order == "desc":
                        query = query.where(time_column > cursor)
                    else:
                        query = query.where(time_column < cursor)

            # Apply sorting
            if sort_order == "desc":
                query = query.order_by(time_column.desc())
            else:
                query = query.order_by(time_column.asc())

            # For "previous" direction, we need to reverse the sort temporarily
            if direction == "previous":
                if sort_order == "desc":
                    query = query.order_by(time_column.asc())
                else:
                    query = query.order_by(time_column.desc())

            # Get one extra item to check if there are more pages
            query = query.limit(limit + 1)

            result = await self.db.execute(query)
            items = list(result.scalars().all())

            # Check if there are more items
            has_more = len(items) > limit
            if has_more:
                items = items[:limit]  # Remove the extra item

            # For "previous" direction, reverse the items back to correct order
            if direction == "previous":
                items = items[::-1]

            # Determine pagination metadata
            has_next = False
            has_previous = False
            next_cursor = None
            previous_cursor = None

            if items:
                if direction == "next":
                    has_next = has_more
                    has_previous = cursor is not None
                    if has_next:
                        next_cursor = getattr(items[-1], time_field)
                    if has_previous:
                        previous_cursor = getattr(items[0], time_field)
                else:  # previous
                    has_previous = has_more
                    has_next = cursor is not None
                    if has_previous:
                        previous_cursor = getattr(items[0], time_field)
                    if has_next:
                        next_cursor = getattr(items[-1], time_field)

            # Get total count if requested (expensive operation)
            total_count = None
            if include_total_count:
                count_query = select(func.count(self._model.id))
                if filters:
                    count_query = count_query.filter_by(**filters)  # type: ignore
                count_result = await self.db.execute(count_query)
                total_count = count_result.scalar()

            return TimeBasedPaginationResult(
                items=items,
                has_next=has_next,
                has_previous=has_previous,
                next_cursor=next_cursor,
                previous_cursor=previous_cursor,
                total_count=total_count,
            )

        except SQLAlchemyError as exc:
            logger.error(f"Failed to paginate {self._model.__name__} by time: {exc}")
            raise RepositoryError(f"Failed to paginate by time: {str(exc)}") from exc

    async def get_items_since(
        self,
        since: datetime,
        time_field: str = "created_at",
        limit: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[ModelType]:
        """
        Get all items created/updated since a specific timestamp.

        Args:
            since: The timestamp to filter from
            time_field: The timestamp field to use for filtering
            limit: Optional limit on number of results
            filters: Additional filter criteria

        Returns:
            List of items since the specified timestamp
        """
        try:
            if not hasattr(self._model, time_field):
                raise RepositoryError(
                    f"Time field '{time_field}' does not exist on {self._model.__name__}"
                )

            time_column = getattr(self._model, time_field)
            query = select(self._model).where(time_column >= since).order_by(time_column.asc())  # type: ignore

            if filters:
                query = query.filter_by(**filters)  # type: ignore

            if limit:
                query = query.limit(limit)

            result = await self.db.execute(query)
            return result.scalars().all()

        except SQLAlchemyError as exc:
            logger.error(f"Failed to get {self._model.__name__} items since {since}: {exc}")
            raise RepositoryError(f"Failed to get items since timestamp: {str(exc)}") from exc

    async def get_items_between(
        self,
        start: datetime,
        end: datetime,
        time_field: str = "created_at",
        sort_order: str = "asc",
        limit: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[ModelType]:
        """
        Get items between two timestamps.

        Args:
            start: Start timestamp (inclusive)
            end: End timestamp (inclusive)
            time_field: The timestamp field to use for filtering
            sort_order: Sort order ("asc" or "desc")
            limit: Optional limit on number of results
            filters: Additional filter criteria

        Returns:
            List of items between the specified timestamps
        """
        try:
            if not hasattr(self._model, time_field):
                raise RepositoryError(
                    f"Time field '{time_field}' does not exist on {self._model.__name__}"
                )

            time_column = getattr(self._model, time_field)
            query = select(self._model).where(time_column >= start, time_column <= end)  # type: ignore

            # Apply sorting
            if sort_order == "desc":
                query = query.order_by(time_column.desc())
            else:
                query = query.order_by(time_column.asc())

            if filters:
                query = query.filter_by(**filters)  # type: ignore

            if limit:
                query = query.limit(limit)

            result = await self.db.execute(query)
            return result.scalars().all()

        except SQLAlchemyError as exc:
            logger.error(
                f"Failed to get {self._model.__name__} items between {start} and {end}: {exc}"
            )
            raise RepositoryError(f"Failed to get items between timestamps: {str(exc)}") from exc

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
