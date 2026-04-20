""" This class holds methods to be used by data_manager when making API calls to help deal with caching """

from pathlib import Path
import requests
import json

API_URL = "https://www.thebluealliance.com/api/v3/"
KEY_NAME =  "X-TBA-Auth-Key"
API_TOKEN = "NvwzlQxqO6BHmjT2cHdNDdgZlQSxdvbMrc8DiP7saThVURWSdtYhUUr0H4RcHRw7"
CACHE_KEY = "If-None-Match"


def call(endpoint: str):
    file_path = Path("cache/" + endpoint + ".json")

    header = {
        KEY_NAME: API_TOKEN,
        # CACHE_KEY: 'W/"5f1544278ec04ed84f1d7c6e80e1ff3333a0e467"'
    }

    if file_path.is_file():
        with open("cache/" + endpoint + ".json", 'r') as f:
            text = json.load(f)
            with open("cache/bypass.json", 'r') as f2:
                text2 = json.load(f2)
                if endpoint in text2['endpoints']:
                    return text['data']
            
            header[CACHE_KEY] = text['etag']

    else:
        file_path.parent.mkdir(parents=True, exist_ok=True)

    # print("REQUEST AHAHHAHAHHAHAHAHHA")
    resp = requests.get(API_URL + endpoint, headers=header)

    if resp.status_code == 404:
        return

    if resp.status_code == 304:
        if file_path.is_file():
            with open("cache/" + endpoint + ".json", 'r') as f:
                text = json.load(f)

                return text['data']

    # print(resp.headers)
    # print(resp.json())


    esc_header = resp.headers['etag'].replace('"', '\\"')


    with open("cache/" + endpoint + ".json", 'w') as f:
        f.write("{\"etag\": \"" + esc_header + "\",\n \"data\": " + json.dumps(resp.json(), indent=4) + "}")

    return resp.json()
