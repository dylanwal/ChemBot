"""
https://funprojects.blog/2019/11/08/rabbitmq-rest-api/
"""

# importing the requests library
import requests
import json

# defining the api-endpoint
API_ENDPOINT = "http://127.0.0.1:15672/api/exchanges/%2f/chembot/publish"

# your source code here

headers = {'content-type': 'application/json'}
# data to be sent to api

pdata = {'properties': {}, 'routing_key': 'chembot.deep_red',
         'payload': '{"action": "set_power", "value": 10}',
         'payload_encoding': 'string'}

# sending post request and saving response as response object
r = requests.post(url=API_ENDPOINT, auth=('guest', 'guest'), json=pdata, headers=headers)

# extracting response text
pastebin_url = r.text
print("Response :%s" % pastebin_url)

