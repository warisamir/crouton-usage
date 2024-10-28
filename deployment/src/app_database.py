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



class DatabasesCRUDRouter(CRUDGenerator[PYDANTIC_SCHEMA]):
    def __init__(
        self,
        schema: Type[PYDANTIC_SCHEMA],
        table: "Table",
        database: "Database",
        create_schema: Optional[Type[PYDANTIC_SCHEMA]] = None,
        update_schema: Optional[Type[PYDANTIC_SCHEMA]] = None,
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
            databases_installed
        ), "Databases and SQLAlchemy must be installed to use the DatabasesCRUDRouter."

        self.table = table
        self.db = database
        self._pk = database.primary_key.columns.values()[0].name
        self._pk_col = self.table.c[self._pk]
        self._pk_type: type = get_pk_type(schema, self._pk)

        super().__init__(
            schema=schema,
            create_schema=create_schema,
            update_schema=update_schema,
            prefix=prefix or table.name,
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
        async def route(
            pagination: PAGINATION = self.pagination,
        ) -> List[Model]:
            skip, limit = pagination.get("skip"), pagination.get("limit")

            query = self.table.select().limit(limit).offset(skip)
            return pydantify_record(await self.db.fetch_all(query))  # type: ignore

        return route

    def _get_one(self, *args: Any, **kwargs: Any) -> CALLABLE:
        async def route(item_id: self._pk_type) -> Model:  # type: ignore
            query = self.table.select().where(self._pk_col == item_id)
            model = await self.db.fetch_one(query)

            if model:
                return pydantify_record(model)  # type: ignore
            else:
                raise NOT_FOUND

        return route

    def _create(self, *args: Any, **kwargs: Any) -> CALLABLE:
        async def route(
            schema: self.create_schema,  # type: ignore
        ) -> Model:
            query = self.table.insert()

            try:
                rid = await self.db.execute(query=query, values=schema.dict())
                if type(rid) is not self._pk_type:
                    rid = getattr(schema, self._pk, rid)

                return await self._get_one()(rid)
            except Exception:
                raise HTTPException(422, "Key already exists") from None

        return route

    def _update(self, *args: Any, **kwargs: Any) -> CALLABLE:
        async def route(
            item_id: self._pk_type, schema: self.update_schema  # type: ignore
        ) -> Model:
            query = self.table.update().where(self._pk_col == item_id)

            try:
                await self.db.fetch_one(
                    query=query, values=schema.dict(exclude={self._pk})
                )
                return await self._get_one()(item_id)
            except Exception as e:
                raise NOT_FOUND from e

        return route

    def _delete_all(self, *args: Any, **kwargs: Any) -> CALLABLE_LIST:
        async def route() -> List[Model]:
            query = self.table.delete()
            await self.db.execute(query=query)

            return await self._get_all()(pagination={"skip": 0, "limit": None})

        return route

    def _delete_one(self, *args: Any, **kwargs: Any) -> CALLABLE:
        async def route(item_id: self._pk_type) -> Model:  # type: ignore
            query = self.table.delete().where(self._pk_col == item_id)

            try:
                row = await self._get_one()(item_id)
                await self.db.execute(query=query)
                return row
            except Exception as e:
                raise NOT_FOUND from e

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

        router = DatabasesCRUDRouter(
            schema=each["schema"],
            table=each["schema"],
            database=each["db_model"],
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
