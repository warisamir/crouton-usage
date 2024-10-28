from fastapi_crudrouter.core._base import *
from fastapi_crudrouter.core.sqlalchemy import *
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import event
import models
import schemas
from database import SessionLocal, engine
from depends import get_api_key
from typing import List, Type, TypeVar, Any, cast
from pydantic import create_model


try:
    from sqlalchemy.sql.schema import Table
    from databases.core import Database
except ImportError:
    Database = None  # type: ignore
    Table = None
    databases_installed = False
else:
    databases_installed = True

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
from fastapi_crudrouter.core._types import PAGINATION, PYDANTIC_SCHEMA, DEPENDENCIES


get_pk_type = get_pk_type_patch
schema_factory = schema_factory_patch


class MemoryCRUDRouter(CRUDGenerator[SCHEMA]):
    def __init__(
        self,
        schema: Type[SCHEMA],
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
        super().__init__(
            schema=schema,
            create_schema=create_schema,
            update_schema=update_schema,
            prefix=prefix,
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

        self.models: List[SCHEMA] = []
        self._id = 1

    def _get_all(self, *args: Any, **kwargs: Any) -> CALLABLE_LIST:
        def route(pagination: PAGINATION = self.pagination) -> List[SCHEMA]:
            skip, limit = pagination.get("skip"), pagination.get("limit")
            skip = cast(int, skip)

            return (
                self.models[skip:]
                if limit is None
                else self.models[skip : skip + limit]
            )

        return route

    def _get_one(self, *args: Any, **kwargs: Any) -> CALLABLE:
        def route(item_id: int) -> SCHEMA:
            for model in self.models:
                if model.id == item_id:  # type: ignore
                    return model

            raise NOT_FOUND

        return route

    def _create(self, *args: Any, **kwargs: Any) -> CALLABLE:
        def route(model: self.create_schema) -> SCHEMA:  # type: ignore
            model_dict = model.dict()
            model_dict["id"] = self._get_next_id()
            ready_model = self.schema(**model_dict)
            self.models.append(ready_model)
            return ready_model

        return route

    def _update(self, *args: Any, **kwargs: Any) -> CALLABLE:
        def route(item_id: int, model: self.update_schema) -> SCHEMA:  # type: ignore
            for ind, model_ in enumerate(self.models):
                if model_.id == item_id:  # type: ignore
                    self.models[ind] = self.schema(
                        **model.dict(), id=model_.id  # type: ignore
                    )
                    return self.models[ind]

            raise NOT_FOUND

        return route

    def _delete_all(self, *args: Any, **kwargs: Any) -> CALLABLE_LIST:
        def route() -> List[SCHEMA]:
            self.models = []
            return self.models

        return route

    def _delete_one(self, *args: Any, **kwargs: Any) -> CALLABLE:
        def route(item_id: int) -> SCHEMA:
            for ind, model in enumerate(self.models):
                if model.id == item_id:  # type: ignore
                    del self.models[ind]
                    return model

            raise NOT_FOUND

        return route

    def _get_next_id(self) -> int:
        id_ = self._id
        self._id += 1

        return id_


def create_route_objects(components: List[str]) -> List:
    routes_to_create = []
    for each in components:
        schema = schemas.__getattribute__(each)
        create_schema = schemas.__getattribute__(each + "Create")
        update_schema = schemas.__getattribute__(each + "Update")

        obj = {
            "schema": schema,
            "create_schema": create_schema,
            "update_schema": update_schema,
            "prefix": each.lower(), 
        }

        routes_to_create.append(obj)
    return routes_to_create

def create_routers(routes_to_create: List) -> List:
    routers = []
    for each in routes_to_create:
        router = MemoryCRUDRouter(
                schema=each["schema"],
                create_schema=each["create_schema"],
                update_schema=each["update_schema"],
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


components = ["User", "Item"]  

routes_to_create = create_route_objects(components)
list_of_routers = create_routers(routes_to_create)
attach_list_of_routers(app, list_of_routers)

@app.on_event("startup")
def startup():
    event.listen(engine, "connect", lambda c, _: c.execute("pragma foreign_keys=on"))
