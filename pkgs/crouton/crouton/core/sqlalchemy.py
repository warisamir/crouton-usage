from typing import Any, Callable, List, Type, Generator, Optional, Union, Dict

from fastapi import Depends, HTTPException, Request
from . import CRUDGenerator, NOT_FOUND, _utils
from ._types import DEPENDENCIES, PAGINATION, PYDANTIC_SCHEMA as SCHEMA

try:
    from sqlalchemy.orm import Session
    from sqlalchemy.ext.declarative import DeclarativeMeta as Model
    from sqlalchemy.exc import IntegrityError
except ImportError:
    Model = None
    Session = None
    IntegrityError = None
    sqlalchemy_installed = False
else:
    sqlalchemy_installed = True
    Session = Callable[..., Generator[Session, Any, None]]

CALLABLE = Callable[..., Model]
CALLABLE_LIST = Callable[..., List[Model]]


# Utility function for extracting query parameters
def query_params(request: Request) -> Dict[str, Any]:
    """
    Extract query parameters from the incoming request
    and return them as a dictionary.
    """
    return dict(request.query_params)


class SQLAlchemyCRUDRouter(CRUDGenerator[SCHEMA]):
    def __init__(
        self,
        schema: Type[SCHEMA],
        db_model: Model,
        db: "Session",
        create_schema: Optional[Type[SCHEMA]] = None,
        update_schema: Optional[Type[SCHEMA]] = None,
        prefix: Optional[str] = None,
        tags: Optional[List[str]] = None,
        paginate: Optional[int] = None,
        get_all_route: Union[bool, DEPENDENCIES] = True,
        get_one_route: Union[bool, DEPENDENCIES] = True,
        create_route: Union[bool, DEPENDENCIES] = True,
        update_route: Union[bool, DEPENDENCIES] = True,
        delete_one_route: Union[bool, DEPENDENCIES] = True,
        delete_all_route: Union[bool, DEPENDENCIES] = True,
        **kwargs: Any
    ) -> None:
        assert (
            sqlalchemy_installed
        ), "SQLAlchemy must be installed to use the SQLAlchemyCRUDRouter."

        self.db_model = db_model
        self.db_func = db
        self._pk: str = db_model.__table__.primary_key.columns.keys()[0]
        self._pk_type: type = _utils.get_pk_type(schema, self._pk)

        super().__init__(
            schema=schema,
            create_schema=create_schema,
            update_schema=update_schema,
            prefix=prefix or db_model.__tablename__,
            tags=tags,
            paginate=paginate,
            get_all_route=get_all_route,
            get_one_route=get_one_route,
            create_route=create_route,
            update_route=update_route,
            delete_one_route=delete_one_route,
            delete_all_route=delete_all_route,
            **kwargs,
        )

    def _parse_query_params(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse query parameters into filters for the database query.
        Exclude pagination-related parameters like 'skip' and 'limit'.
        """
        filters = {}
        accepted_fields = self.db_model.__table__.columns
    
        # Exclude pagination-related parameters
        excluded_params = {"skip", "limit"}
    
        for key, value in query_params.items():
            if key in excluded_params:
                continue  # Skip pagination parameters
            if key in accepted_fields:
                column = getattr(self.db_model, key)
                try:
                    column_type = column.type.python_type
                    parsed_value = column_type(value)
                    filters[key] = parsed_value
                except (ValueError, TypeError) as e:
                    raise HTTPException(
                        status_code=422, detail=f"Invalid value for {key}: {e}"
                    )
            else:
                raise HTTPException(400, f"Invalid filter field: {key}")
    
        return filters


    def _get_all(self, *args: Any, **kwargs: Any) -> CALLABLE_LIST:
        def route(
            db: Session = Depends(self.db_func),
            pagination: PAGINATION = self.pagination,
            query_params: Dict[str, Any] = Depends(query_params),
        ) -> List[Model]:
            skip = pagination.get("skip", 0)
            limit = pagination.get("limit", 100)  # Default values if not provided
    
            # Parse and validate query parameters
            filters = self._parse_query_params(query_params)
    
            # Apply filters to the query
            db_models: Model = (
                db.query(self.db_model)
                .filter_by(**filters)
                .order_by(getattr(self.db_model, self._pk))
                .limit(limit)
                .offset(skip)
                .all()
            )
    
            if db_models:
                return db_models
            else:
                raise NOT_FOUND from None
    
        return route


    def _get_one(self, *args: Any, **kwargs: Any) -> CALLABLE:
        def route(
            item_id: self._pk_type, db: Session = Depends(self.db_func)  # type: ignore
        ) -> Model:
            model: Model = db.query(self.db_model).get(item_id)

            if model:
                return model
            else:
                raise NOT_FOUND from None

        return route

    def _create(self, *args: Any, **kwargs: Any) -> CALLABLE:
        def route(
            model: self.create_schema,  # type: ignore
            db: Session = Depends(self.db_func),
        ) -> Model:
            try:
                db_model: Model = self.db_model(**model.dict())
                db.add(db_model)
                db.commit()
                db.refresh(db_model)
                return db_model
            except IntegrityError:
                db.rollback()
                raise HTTPException(422, "Key already exists") from None

        return route

    def _update(self, *args: Any, **kwargs: Any) -> CALLABLE:
        def route(
            item_id: self._pk_type,  # type: ignore
            model: self.update_schema,  # type: ignore
            db: Session = Depends(self.db_func),
        ) -> Model:
            try:
                db_model: Model = self._get_one()(item_id, db)

                for key, value in model.dict(exclude={self._pk}).items():
                    if hasattr(db_model, key):
                        setattr(db_model, key, value)

                db.commit()
                db.refresh(db_model)

                return db_model
            except IntegrityError as e:
                db.rollback()
                self._raise(e)

        return route

    def _delete_all(self, *args: Any, **kwargs: Any) -> CALLABLE_LIST:
        def route(db: Session = Depends(self.db_func)) -> List[Model]:
            db.query(self.db_model).delete()
            db.commit()

            return self._get_all()(db=db, pagination={"skip": 0, "limit": None})

        return route

    def _delete_one(self, *args: Any, **kwargs: Any) -> CALLABLE:
        def route(
            item_id: self._pk_type, db: Session = Depends(self.db_func)  # type: ignore
        ) -> Model:
            db_model: Model = self._get_one()(item_id, db)
            db.delete(db_model)
            db.commit()

            return db_model

        return route
