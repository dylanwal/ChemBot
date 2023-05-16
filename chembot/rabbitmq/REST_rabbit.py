
import requests

from chembot.configuration import config
from chembot.rabbitmq.messages import RabbitMessage


def write_message(message: RabbitMessage):
    write(message.destination, message.to_JSON())

#####


def create_exchange():
    pass


def create_queue(
    queue: str,
    ip: str = config.rabbit_host,
    port: int = config.rabbit_port

):
    API = f"http://{ip}:{port}/api/queues/%2f/{queue}"
    headers = {'content-type': 'application/json'}
    pdata = {"type": "topic", "auto_delete": True, "durable": False, "internal": False, "arguments": {}}

    # sending post request and saving response as response object
    reply = requests.put(url=API, auth=('guest', 'guest'), json=pdata, headers=headers)

    # extracting response text
    pastebin_url = reply.text
    print("Response :%s" % pastebin_url)
    # expected resoince {"routed": true}


def create_binding():
    pass


def write(
        routing_key: str,
        payload: str,
        exchange: str = config.rabbit_exchange,
        ip: str = config.rabbit_host,
        port: int = config.rabbit_port
):
    API = f"http://{ip}:{port}/api/exchanges/%2f/{exchange}/publish"
    headers = {'content-type': 'application/json'}
    pdata = {'properties': {}, 'routing_key': routing_key, 'payload': payload, 'payload_encoding': 'string'}

    # sending post request and saving response as response object
    reply = requests.post(url=API, auth=('guest', 'guest'), json=pdata, headers=headers)

    # extracting response text
    pastebin_url = reply.text
    print("Response :%s" % pastebin_url)
    # expected resoince {"routed": true}


def read(ip: str, port: int, exchange: str, routing_key: str, payload: str):
    API = f"http://{ip}:{port}/api/exchanges/%2f/{exchange}/publish"
    headers = {'content-type': 'application/json'}
    pdata = {'count': '5', 'requeue': 'true', 'encoding': 'auto', 'truncate': '50000'}

    # sending post request and saving response as response object
    r = requests.post(url=API_ENDPOINT, auth=('pete', 'pete'), json=pdata, headers=headers)

    # extracting response text
    pastebin_url = r.text
    print("Response :%s" % pastebin_url)
