import requests
import json
import os

if os.environ.get("LEDA_DEV") == "dev":
    SEARCH_ENGINE_API_BASE_URL = "http://127.0.0.1:5000"
else:
    SEARCH_ENGINE_API_BASE_URL = "http://157.245.70.211:5000"


def get_search_results(features, query=None):
    url = f"{SEARCH_ENGINE_API_BASE_URL}/search"
    data = json.dumps({"query": query, "features": features})
    resp = requests.get(url, json=data)
    return resp.json()['data']


def get_report(features, business_cases):
    url = f"{SEARCH_ENGINE_API_BASE_URL}/generate_report"
    data = json.dumps({"features": features, "business_cases": business_cases})
    resp = requests.get(url, json=data)
    report_url = f"{SEARCH_ENGINE_API_BASE_URL}/{resp.json()['data']}"
    return report_url


def get_questions():
    url = f"{SEARCH_ENGINE_API_BASE_URL}/get_questions"
    try:
        resp = requests.get(url).json()['data']
    except requests.exceptions.ConnectionError:
        print("---------> !!!! Search Engine API is down")
        resp = []
    return resp


def get_sector_description(sector):
    url = f"{SEARCH_ENGINE_API_BASE_URL}/get_sector_description/{sector}"
    resp = requests.get(url)
    return resp.json()['data']


def get_bc_attribute_list(attribute, filter=None):
    url = f"{SEARCH_ENGINE_API_BASE_URL}/get_bc_attribute_list/{attribute}"
    data = json.dumps({"filter": filter})
    resp = requests.get(url, json=data)
    return resp.json()['data']
