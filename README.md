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
from pydantic import BaseModel
from fastapi import FastAPI
from crouton import SQLAlchemyCRUDRouter as CRUDRouter

class Potato(BaseModel):
    id: int
    color: str
    mass: float

app = FastAPI()
app.include_router(CRUDRouter(schema=Potato))
```

# Example
![image](https://github.com/user-attachments/assets/22e6ce3a-6eb1-4a80-a37f-93fef545b49e)
