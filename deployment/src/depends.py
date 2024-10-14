from fastapi import Request, Security, HTTPException
from fastapi.security.api_key import APIKeyQuery
import inspect
from dotenv import load_dotenv
load_dotenv()

API_KEY_NAME = os.getenv("DEPENDS_API_KEY_NAME")
API_KEY_VALUE = os.getenv("DEPENDS_API_KEY_VALUE")
api_key_query = APIKeyQuery(name=API_KEY_NAME, auto_error=False)


def get_api_key(access_token: str = Security(api_key_query)):
    if access_token != API_KEY_VALUE:
        raise HTTPException(401, "Invalid token")