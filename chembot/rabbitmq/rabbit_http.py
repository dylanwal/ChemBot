"""
Many more http methods are available. see RabbitMQ docs


"""
import json

import requests

from chembot.configuration import config


def get_vhost(
        ip: str = config.rabbit_host,
        port: int = config.rabbit_port,
) -> list[dict]:
    """server definitions for a given virtual host"""
    reply = requests.get(f"http://{ip}:{port}/api/vhosts", auth=config.rabbit_auth)
    return json.loads(reply.text)


def create_exchange(
        exchange: str,
        ip: str = config.rabbit_host,
        port: int = config.rabbit_port,
        type_: str = "direct",
        auto_delete: bool = False,
        durable: bool = True,
        internal: bool = False,
        arguments: dict = None
):
    API = f"http://{ip}:{port}/api/exchanges/%2f/{exchange}"
    headers = {'content-type': 'application/json'}
    pdata = {
        "type": type_,
        "auto_delete": auto_delete,
        "durable": durable,
        "internal": internal,
        "arguments": arguments if arguments is not None else {}
    }
    reply = requests.put(url=API, auth=config.rabbit_auth, json=pdata, headers=headers)

    if not reply.ok:
        raise ValueError(f"Error creating a exchange. status code: {reply.status_code}")


def create_queue(
        queue: str,
        ip: str = config.rabbit_host,
        port: int = config.rabbit_port,
        auto_delete: bool = False,
        durable: bool = True,
        arguments: dict = None
):
    API = f"http://{ip}:{port}/api/queues/%2f/{queue}"
    headers = {'content-type': 'application/json'}
    pdata = {
        "auto_delete": auto_delete,
        "durable": durable,
        "arguments": arguments if arguments is not None else {},
        # "node":"rabbit@smacmullen"
    }
    reply = requests.put(url=API, auth=config.rabbit_auth, json=pdata, headers=headers)

    if not reply.ok:
        raise ValueError(f"Error creating a queue. status code: {reply.status_code}")


def create_binding(
        queue: str,
        exchange: str = config.rabbit_exchange,
        ip: str = config.rabbit_host,
        port: int = config.rabbit_port
):
    API = f"http://{ip}:{port}/api/bindings/%2f/e/{exchange}/q/{queue}"
    headers = {'content-type': 'application/json'}
    reply = requests.post(url=API, auth=config.rabbit_auth, headers=headers)

    if not reply.ok:
        raise ValueError(f"Error binding queue ({queue}) to exchange ({exchange}). status code: {reply.status_code}")


def publish(
        routing_key: str,
        payload: str,
        exchange: str = config.rabbit_exchange,
        ip: str = config.rabbit_host,
        port: int = config.rabbit_port
):
    API = f"http://{ip}:{port}/api/exchanges/%2f/{exchange}/publish"
    headers = {'content-type': 'application/json'}
    pdata = {'properties': {}, 'routing_key': routing_key, 'payload': payload, 'payload_encoding': 'string'}
    reply = requests.post(url=API, auth=config.rabbit_auth, json=pdata, headers=headers)

    if not reply.ok:
        raise ValueError(f"Error publishing message to exchange {exchange}. status code: {reply.status_code}")

    reply_dict = json.loads(reply.text)
    if not reply_dict["routed"]:
        raise ValueError(f"Error publishing message to exchange {exchange}. Routing invalid.")


def get(
        queue: str,
        ip: str = config.rabbit_host,
        port: int = config.rabbit_port,
        count: int = 1,
        ackmode: str = "ack_requeue_true",
        encoding: str = "auto",
        truncate: str = 50_000
        ) -> list[dict]:
    """

    Parameters
    ----------
    queue
    ip
    port
    count
        controls the maximum number of messages to get.
        You may get fewer messages than this if the queue cannot immediately provide them.
    ackmode
        determines whether the messages will be removed from the queue.
        If ackmode is ack_requeue_true or reject_requeue_true they will be requeued -
        if ackmode is ack_requeue_false or reject_requeue_false they will be removed.
    encoding
        must be either "auto" (in which case the payload will be returned as a string if it is valid UTF-8,
        and base64 encoded otherwise), or "base64" (in which case the payload will always be base64 encoded).
    truncate
        the message payload if it is larger than the size given (in bytes).

    Returns
    -------

    """
    API = f"http://{ip}:{port}/api/queues/%2f/{queue}/get"
    headers = {'content-type': 'application/json'}
    pdata = {"count": count, "ackmode": ackmode, "encoding": encoding, "truncate": truncate}

    # sending post request and saving response as response object
    reply = requests.post(url=API, auth=config.rabbit_auth, json=pdata, headers=headers)

    if not reply.ok:
        raise ValueError(f"Error getting message from queue {queue}. status code: {reply.status_code}")

    reply_list = json.loads(reply.text)
    return [json.loads(message["payload"]) for message in reply_list]
