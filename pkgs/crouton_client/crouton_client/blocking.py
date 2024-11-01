import requests as r
import logging
from .UUID import UUIDGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CroutonClient:
    def __init__(self, API_ROOT, ACCESS_STRING):
        self.API_ROOT = API_ROOT
        self.ACCESS_STRING = ACCESS_STRING

    def api_get_call(self, resource: str, item_id: str = None):
        if item_id:
            res = r.get(self.API_ROOT + resource + '/' + item_id + self.ACCESS_STRING)
        else:
            res = r.get(self.API_ROOT + resource + self.ACCESS_STRING)
            
        if res.status_code == 200:
            return res.model_dump_json()
        else:
            logger.error(f"GET request failed with status {res.status_code}: {res.model_dump_json()}")
            raise ValueError(res.status_code)

    def api_post_call(self, resource: str, data_obj: dict):
        if 'id' not in data_obj:
            data_obj.update({'id': UUIDGenerator().create()})
            
        res = r.post(self.API_ROOT + resource + self.ACCESS_STRING, json=data_obj)
        
        if res.status_code == 200:
            return res.model_dump_json()
        else:
            logger.error(f"POST request failed with status {res.status_code}: {res.model_dump_json()}")
            raise ValueError(res.status_code)

    def api_put_call(self, resource: str, data_obj: dict, item_id: str):
        res = r.put(self.API_ROOT + resource + '/' + item_id + self.ACCESS_STRING, json=data_obj)
        
        if res.status_code == 200:
            return res.model_dump_json()
        else:
            logger.error(f"PUT request failed with status {res.status_code}: {res.model_dump_json()}")
            raise ValueError(res.status_code)

    def api_delete_call(self, resource: str, item_id: str = None):
        if item_id:
            res = r.delete(self.API_ROOT + resource + '/' + item_id + self.ACCESS_STRING)
        else:
            res = r.delete(self.API_ROOT + resource + self.ACCESS_STRING)
            
        if res.status_code == 200:
            return res.model_dump_json()
        else:
            logger.error(f"DELETE request failed with status {res.status_code}: {res.model_dump_json()}")
            raise ValueError(res.status_code)
