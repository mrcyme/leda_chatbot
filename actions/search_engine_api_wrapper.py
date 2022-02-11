import requests
import json

SEARCH_ENGINE_API_BASE_URL = "http://127.0.0.1:5000/"


def get(features, query=None):
    url = f"{SEARCH_ENGINE_API_BASE_URL}/search"
    data = json.dumps({"query": query, "features": features})
    resp = requests.get(url, json=data)
    return resp.json()['data']


#print(get("I work in healthcare, sensor data weelchair",{"sector": "healthcare"}))
