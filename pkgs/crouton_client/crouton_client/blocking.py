import requests as r
import logging
from urllib.parse import urlencode
from typing import Optional, Any, Dict
from .UUID import UUIDGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CroutonClient:
    def __init__(self, API_ROOT: str, ACCESS_STRING: Optional[str] = None):
        self.API_ROOT = API_ROOT.rstrip('/')  # Ensure no trailing slash
        self.ACCESS_STRING = ACCESS_STRING

    def _build_url(self, resource: str, item_id: Optional[str] = None, query_params: Optional[dict] = None) -> str:
        """
        Helper method to construct the URL with resource, item_id, and query parameters.
        """
        url = f"{self.API_ROOT}/{resource.strip('/')}"
        
        # Add item ID if provided
        if item_id:
            url += f"/{item_id}"

        # Add query parameters
        if query_params:
            query_string = urlencode(query_params)
            url += f"?{query_string}"

        # Add access string as a query parameter
        if self.ACCESS_STRING:
            separator = '&' if '?' in url else '?'
            url += f"{separator}token={self.ACCESS_STRING.strip('?')}"

        return url

    def api_get_call(
        self, 
        resource: str, 
        item_id: Optional[str] = None, 
        filter_key: Optional[str] = None, 
        filter_value: Optional[str] = None
    ) -> dict:
        """
        Perform a GET request with optional filters and an item ID.
        """
        query_params = {filter_key: filter_value} if filter_key and filter_value else None
        url = self._build_url(resource, item_id, query_params)

        logger.info(f"Performing GET request to {url}")
        res = r.get(url)
        if res.status_code == 200:
            return res.json()
        else:
            logger.error(f"GET request failed with status {res.status_code}: {res.text}")
            raise ValueError(f"GET request failed with status {res.status_code}: {res.text}")

    def api_post_call(self, resource: str, data_obj: dict) -> dict:
        """
        Perform a POST request to create a resource.
        """
        if 'id' not in data_obj:
            data_obj['id'] = UUIDGenerator().create()

        url = self._build_url(resource)

        logger.info(f"Performing POST request to {url} with data {data_obj}")
        res = r.post(url, json=data_obj)
        if res.status_code == 200:
            return res.json()
        else:
            logger.error(f"POST request failed with status {res.status_code}: {res.text}")
            raise ValueError(f"POST request failed with status {res.status_code}: {res.text}")

    def api_put_call(self, resource: str, data_obj: dict, item_id: str) -> dict:
        """
        Perform a PUT request to update a resource.
        """
        url = self._build_url(resource, item_id)

        logger.info(f"Performing PUT request to {url} with data {data_obj}")
        res = r.put(url, json=data_obj)
        if res.status_code == 200:
            return res.json()
        else:
            logger.error(f"PUT request failed with status {res.status_code}: {res.text}")
            raise ValueError(f"PUT request failed with status {res.status_code}: {res.text}")

    def api_delete_call(self, resource: str, item_id: Optional[str] = None) -> dict:
        """
        Perform a DELETE request to delete a resource.
        """
        url = self._build_url(resource, item_id)

        logger.info(f"Performing DELETE request to {url}")
        res = r.delete(url)
        if res.status_code == 200:
            return res.json()
        else:
            logger.error(f"DELETE request failed with status {res.status_code}: {res.text}")
            raise ValueError(f"DELETE request failed with status {res.status_code}: {res.text}")
