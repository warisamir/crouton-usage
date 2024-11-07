import requests as r
import logging
from .UUID import UUIDGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AsyncCroutonClient:
    def __init__(self, API_ROOT, ACCESS_STRING):
        self.API_ROOT = API_ROOT
        self.ACCESS_STRING = ACCESS_STRING
            
    async def get(self, resource: str, item_id: str = None, filters: dict = None):
        url = self.API_ROOT + resource
        
        # Start with the access string if necessary
        query_params = {}
        
        if filters:
            query_params.update(filters)  # Add the filters to the query parameters

        # Always add the access token at the end of the query string
        query_params['access_token'] = self.ACCESS_STRING.strip("?")  # Remove any extra '?' if included in ACCESS_STRING

        # Construct the full query string from the dictionary
        query_string = "&".join([f"{key}={value}" for key, value in query_params.items()])
        
        # Add the item_id if provided (for specific resource requests)
        if item_id:
            url += f'/{item_id}'

        # Final URL with query parameters
        url += "?" + query_string if query_string else ""
        
        # Perform the GET request
        res = r.get(url)
        if res.status_code == 200:
            return res.model_dump_json()
        else:
            logger.error(f"GET request failed with status {res.status_code}: {res.model_dump_json()}")
            raise ValueError

    async def post(self, resource: str, data_obj: dict):
        if 'id' not in data_obj:
            data_obj.update({'id': UUIDGenerator().create()})
        res = r.post(self.API_ROOT + resource + self.ACCESS_STRING, json=data_obj)
        if res.status_code == 200:
            return res.model_dump_json()
        else:
            logger.error(f"POST request failed with status {res.status_code}: {res.model_dump_json()}")
            raise ValueError

    async def put(self, resource: str, data_obj: dict, item_id: str = None):
        if item_id:
            res = r.put(self.API_ROOT + resource + '/' + item_id + self.ACCESS_STRING, json=data_obj)
            if res.status_code == 200:
                return res.model_dump_json()
            else:
                logger.error(f"PUT request failed with status {res.status_code}: {res.model_dump_json()}")
                raise ValueError

    async def delete(self, resource: str, item_id: str = None):
        if item_id:
            res = r.delete(self.API_ROOT + resource + '/' + item_id + self.ACCESS_STRING)
        else:
            res = r.delete(self.API_ROOT + resource + '/' + item_id + self.ACCESS_STRING)

        if res.status_code == 200:
            return res.model_dump_json()
        else:
            logger.error(f"DELETE request failed with status {res.status_code}: {res.model_dump_json()}")
            raise ValueError
