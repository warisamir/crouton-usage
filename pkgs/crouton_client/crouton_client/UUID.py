import os
from hashlib import sha256
from uuid import UUID, uuid4, uuid5
from pydantic import BaseModel

NAMESPACE_URL_UUID = os.getenv("NAMESPACE_URL_UUID", "default")

class UUIDGenerator(BaseModel):
  namespace: UUID = UUID(NAMESPACE_URL_UUID)


  def create(self):
    name: UUID = str(uuid4())
    return str(uuid5(self.namespace, name))