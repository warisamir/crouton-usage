from fastapi_crudrouter.core._base import *
from fastapi_crudrouter.core.sqlalchemy import *
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import event
from pkg.crouton.core import DatabasesCRUDRouter
from deployment.src.models import models
from deployment.src.schemas import schemas
from deployment.src.database import SessionLocal, engine, SQLALCHEMY_DATABASE_URL
from deployment.src.depends import get_api_key
from typing import List, Type, TypeVar, Any, cast
import databases
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


from fastapi_crudrouter.core._utils import get_pk_type, schema_factory, AttrDict
from fastapi_crudrouter.core._types import PAGINATION, PYDANTIC_SCHEMA, DEPENDENCIES


get_pk_type = get_pk_type_patch
schema_factory = schema_factory_patch




def create_route_objects(components: List[str]) -> List:
    routes_to_create = []
    for each in components:
        schema = schemas.__getattribute__(each)
        create_schema = schemas.__getattribute__(each + "Create")
        update_schema = schemas.__getattribute__(each + "Update")
        database = databases.Database(SQLALCHEMY_DATABASE_URL)
        table = models.__getattribute__(each + "Model").__table__


        obj = {
            "schema": schema,
            "create_schema": create_schema,
            "update_schema": update_schema,
            "database": database,
            "table": table,
            "prefix": each.lower(), 
        }

        routes_to_create.append(obj)
    return routes_to_create

def create_routers(routes_to_create: List) -> List:
    routers = []
    for each in routes_to_create:

        router = DatabasesCRUDRouter(
            schema=each["schema"],
            table=each["table"],
            database=each["database"],
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
