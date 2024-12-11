# Stable Release Installation
```python
pip install crouton
```

# Development Release Installation
```python
pip install package-name --pre
```

# Basic Usage
Below is a simple example of what the CRUDRouter can do. In just ten lines of code, you can generate all the crud routes you need for any model. A full list of the routes generated can be found here.
```python
from sqlalchemy import Column, String, Float, Integer
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from pydantic import BaseModel
from fastapi import FastAPI
from crouton import SQLAlchemyCRUDRouter

app = FastAPI()
engine = create_engine(
    "sqlite:///./app.db",
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    finally:
        session.close()


class PotatoCreate(BaseModel):
    thickness: float
    mass: float
    color: str
    type: str


class Potato(PotatoCreate):
    id: int

    class Config:
        orm_mode = True


class PotatoModel(Base):
    __tablename__ = 'potatoes'
    id = Column(Integer, primary_key=True, index=True)
    thickness = Column(Float)
    mass = Column(Float)
    color = Column(String)
    type = Column(String)


Base.metadata.create_all(bind=engine)

router = SQLAlchemyCRUDRouter(
    schema=Potato,
    create_schema=PotatoCreate,
    db_model=PotatoModel,
    db=get_db,
    prefix='potato'
)

app.include_router(router)

```

# Example
![image](https://github.com/user-attachments/assets/22e6ce3a-6eb1-4a80-a37f-93fef545b49e)
"# crouton-usage" 
