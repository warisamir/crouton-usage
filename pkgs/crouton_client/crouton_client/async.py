import requests as r
from .UUID import UUIDGenerator

class AsyncCroutonClient:
    def __init__(self, API_ROOT, ACCESS_STRING):
        self.API_ROOT = API_ROOT
        self.ACCESS_STRING = ACCESS_STRING
            
    async def get(self, resource: str, item_id: str = None):
        if item_id:
            res = r.get(self.API_ROOT+resource+'/'+item_id+self.ACCESS_STRING)
            if res.status_code == 200:
                    return res.json()
            else:
                print(res.status_code)
                print(res.json())
                raise ValueError
        else:
            res = r.get(self.API_ROOT+resource+self.ACCESS_STRING)
            if res.status_code == 200:
                    return res.json()
            else:
                print(res.status_code)
                print(res.json())
                raise ValueError


    async def post(self, resource: str, data_obj: dict):
    	if 'id' not in data_obj:
        	data_obj.update({'id': UUIDGenerator().create()})
        res = r.post(self.API_ROOT+resource+self.ACCESS_STRING, 
                json=data_obj)
        if res.status_code == 200:
            return res.json()
        else:
            print(res.status_code)
            print(res.json())
            raise ValueError

    
    async def put(self, resource: str, data_obj: dict, item_id: str = None):
        if item_id:
            res = r.put(self.API_ROOT+resource+'/'+item_id+self.ACCESS_STRING, 
                    json=data_obj)
            if res.status_code == 200:
                return res.json()
            else:
                print(res.status_code)
                print(res.json())
                raise ValueError

    async def delete(self, resource: str, item_id: str = None):
        if item_id:
            res = r.delete(self.API_ROOT+resource+'/'+item_id+self.ACCESS_STRING)
        else:
            res = r.delete(self.API_ROOT+resource+'/'+item_id+self.ACCESS_STRING)

        if res.status_code == 200:
            return res.json()
        else:
            print(res.status_code, res.json())
            raise ValueError 
