from pydantic import BaseModel

# UUID
from hashlib import sha256
from uuid import UUID, uuid4, uuid5


class UUIDGenerator(BaseModel):
  namespace: UUID = UUID(NAMESPACE_URL_UUID)


  def create(self):
    name: UUID = str(uuid4())
    return str(uuid5(self.namespace, name))