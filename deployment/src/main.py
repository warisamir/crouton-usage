from fastapi_crudrouter import SQLAlchemyCRUDRouter
from fastapi import Depends, FastAPI, HTTPException, Request, UploadFile, File, Form
from sqlalchemy.orm import Session
import requests as r
from typing import List, Union

from sqlalchemy import event
import models
import schemas
from database import SessionLocal, engine
import os
from depends import get_api_key
from datetime import datetime


app = FastAPI()
models.Base.metadata.create_all(bind=engine)
event.listen(engine, 'connect', lambda c, _: c.execute('pragma foreign_keys=on'))

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_route_objects(components: List) -> List:
	routes_to_create = []
	
	for each in components:
	    schema = schemas.__getattribute__(each)
	    create_schema = schemas.__getattribute__(each+'Create')
	    update_schema = schemas.__getattribute__(each+'Update')
	    db_model = models.__getattribute__(each+'Model')
	    
	    obj = {'schema': schema,
		   'create_schema': create_schema,
		   'update_schema': update_schema,
		   'db_model': db_model, 
		   'prefix': each}
	    
	    routes_to_create.append(obj)
		
	return routes_to_create


def create_routers(routes_to_create: List) -> List:
	routers = []
	for each in routes_to_create:

		router = SQLAlchemyCRUDRouter(
		schema=each['schema'],
		create_schema=each['create_schema'],
		update_schema=each['update_schema'],
		db_model=each['db_model'],
		db=get_db,
		prefix=each['prefix'],
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

components = ['User']

routes_to_create = create_route_objects(components)
list_of_routers = create_routers(routes_to_create)
attach_list_of_routers(app, list_of_routers)


@app.on_event('startup')
def startup():
    event.listen(engine, 'connect', lambda c, _: c.execute('pragma foreign_keys=on'))