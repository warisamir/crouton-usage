from fastapi_crudrouter.core._base import *
from fastapi_crudrouter.core.sqlalchemy import *
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import event
import models
import schemas
from database import SessionLocal, engine
from depends import get_api_key
from typing import List, Type, TypeVar, Any
from pydantic import create_model

app = FastAPI()
models.Base.metadata.create_all(bind=engine)
event.listen(engine, "connect", lambda c, _: c.execute("pragma foreign_keys=on"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

T = TypeVar('T')

# Pydantic patch methods
def get_pk_type_patch(schema: Type[T], pk_field: str) -> Any:
    try:
        print(schema.__fields__[pk_field].annotation)
        return schema.__fields__[pk_field].annotation  # Use annotation instead of type_
    except KeyError:
        return int  # Fallback to int if the key is not found

def schema_factory_patch(
    schema_cls: Type[T], pk_field_name: str = "id", name: str = "Create"
) -> Type[T]:
    fields = {
        name: (f.annotation, ...)  # Use annotation for field types
        for name, f in schema_cls.__fields__.items()
        if name != pk_field_name
    }
    name = schema_cls.__name__ + name
    return create_model(__model_name=name, **fields)  


from fastapi_crudrouter.core._utils import get_pk_type, schema_factory

get_pk_type = get_pk_type_patch
schema_factory = schema_factory_patch


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
        self._pk_type: type = get_pk_type(schema, self._pk)

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
            **kwargs
        )

    def _get_all(self, *args: Any, **kwargs: Any) -> CALLABLE_LIST:
        def route(
            db: Session = Depends(self.db_func),
            pagination: PAGINATION = self.pagination,
        ) -> List[Model]:
            skip, limit = pagination.get("skip"), pagination.get("limit")

            db_models: List[Model] = (
                db.query(self.db_model)
                .order_by(getattr(self.db_model, self._pk))
                .limit(limit)
                .offset(skip)
                .all()
            )
            return db_models

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




def create_route_objects(components: List[str]) -> List:
    routes_to_create = []
    for each in components:
        schema = schemas.__getattribute__(each)
        create_schema = schemas.__getattribute__(each + "Create")
        update_schema = schemas.__getattribute__(each + "Update")
        db_model = models.__getattribute__(each + "Model")

        obj = {
            "schema": schema,
            "create_schema": create_schema,
            "update_schema": update_schema,
            "db_model": db_model,
            "prefix": each.lower(), 
        }

        routes_to_create.append(obj)
    return routes_to_create

def create_routers(routes_to_create: List) -> List:
    routers = []
    for each in routes_to_create:
        router = SQLAlchemyCRUDRouter(
            schema=each["schema"],
            create_schema=each["create_schema"],
            update_schema=each["update_schema"],
            db_model=each["db_model"],
            db=get_db,
            prefix=each["prefix"],
            get_one_route=[Depends(get_api_key)],
            get_all_route=[Depends(get_api_key)],
            create_route=[Depends(get_api_key)],
            update_route=[Depends(get_api_key)],
            delete_one_route=[Depends(get_api_key)],
            delete_all_route=[Depends(get_api_key)],
        )
        routers.append(router)
    return routers

def attach_list_of_routers(app, list_of_routers):
    for each in list_of_routers:
        app.include_router(each)


components = ["User"]  

routes_to_create = create_route_objects(components)
list_of_routers = create_routers(routes_to_create)
attach_list_of_routers(app, list_of_routers)

@app.on_event("startup")
def startup():
    event.listen(engine, "connect", lambda c, _: c.execute("pragma foreign_keys=on"))