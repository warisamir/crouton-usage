import requests as r
from .UUID import UUIDGenerator

class CroutonClient:
    def __init__(self, API_ROOT, ACCESS_STRING):
        self.API_ROOT = API_ROOT
        self.ACCESS_STRING = ACCESS_STRING

    def api_get_call(resource: str, item_id: str = None):
        if item_id:
            res = r.get(API_ROOT+resource+'/'+item_id+ACCESS_STRING)
            if res.status_code == 200:
                return res.json()
            else:
                print(res.status_code)
                print(res.json())
                
                # Test
                raise ValueError(res.status_code)
        else:
            res = r.get(API_ROOT+resource+ACCESS_STRING)
            if res.status_code == 200:
                return res.json()
            else:
                print(res.status_code)
                print(res.json())
                
                # Test
                raise ValueError(res.json())


    def api_post_call(resource: str, data_obj: dict):
        if 'id' not in data_obj:
                data_obj.update({'id': UUIDGenerator().create()})
        res = r.post(API_ROOT+resource+ACCESS_STRING, 
                json=data_obj)
        if res.status_code == 200:
            return res.json()
        else:
            print(res.status_code)
            print(res.json())
            raise ValueError


    def api_put_call(resource: str, data_obj: dict, item_id: str):
        res = r.put(API_ROOT+resource+'/'+item_id+ACCESS_STRING, 
                json=data_obj)
        if res.status_code == 200:
            return res.json()
        else:
            print(res.status_code)
            print(res.json())
            raise ValueError


    def api_delete_call(resource: str, item_id: str = None):
        if item_id:
            res = r.delete(API_ROOT+resource+'/'+item_id+ACCESS_STRING)
        else:
            res = r.delete(API_ROOT+resource+'/'+item_id+ACCESS_STRING)

        if res.status_code == 200:
            return res.json()
        else:
            print(res.status_code, res.json())
            raise ValueError 

