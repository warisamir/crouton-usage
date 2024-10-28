from datetime import datetime, date
from uuid import UUID
from typing import Union, List, Any, ForwardRef, Optional
import base64
from pydantic import BaseModel, validator, Field, ConfigDict
from fastapi import UploadFile, File
from typing import ForwardRef

class UserUpdate(BaseModel):
    email: str
    password: str
    email_validated: bool = False
    active: bool = True
    temporary_password: bool = False
    last_modified: datetime = datetime.utcnow()

class UserCreate(UserUpdate):
    id: str

class User(UserCreate):
    date_registered: datetime
    model_config = ConfigDict(from_attributes=True)



class ItemModel(BaseModel):
    id: str
    name: str
    barcode: str
    available: bool = False
    total_available: int


class ItemCreate(BaseModel):
    id: str
    barcode: str
    name: str
    available: bool = False
    total_available: int


class ItemUpdate(BaseModel):
    name: str
    available: bool = False
    total_available: int


class Item(ItemCreate):
    model_config = ConfigDict(from_attributes=True)