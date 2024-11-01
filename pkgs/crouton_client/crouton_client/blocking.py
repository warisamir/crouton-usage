import requests as r
from .UUID import UUIDGenerator

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
            return res.json()
        else:
            print(res.status_code)
            print(res.json())
            raise ValueError(res.status_code)

    def api_post_call(self, resource: str, data_obj: dict):
        if 'id' not in data_obj:
            data_obj.update({'id': UUIDGenerator().create()})
            
        res = r.post(self.API_ROOT + resource + self.ACCESS_STRING, json=data_obj)
        
        if res.status_code == 200:
            return res.json()
        else:
            print(res.status_code)
            print(res.json())
            raise ValueError(res.status_code)

    def api_put_call(self, resource: str, data_obj: dict, item_id: str):
        res = r.put(self.API_ROOT + resource + '/' + item_id + self.ACCESS_STRING, json=data_obj)
        
        if res.status_code == 200:
            return res.json()
        else:
            print(res.status_code)
            print(res.json())
            raise ValueError(res.status_code)

    def api_delete_call(self, resource: str, item_id: str = None):
        if item_id:
            res = r.delete(self.API_ROOT + resource + '/' + item_id + self.ACCESS_STRING)
        else:
            res = r.delete(self.API_ROOT + resource + self.ACCESS_STRING)
            
        if res.status_code == 200:
            return res.json()
        else:
            print(res.status_code)
            print(res.json())
            raise ValueError(res.status_code)
