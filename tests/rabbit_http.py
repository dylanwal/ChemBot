import json

from chembot.rabbitmq.rabbit_http import create_exchange, create_queue, create_binding, get, publish


def main():
    create_exchange("test_exchange")
    create_queue("test_queue")
    create_binding("test_queue", "test_exchange")

    publish("", json.dumps({"property_1": 1, "property_2": "fish"}), "test_exchange")

    reply = get("test_queue")
    print(reply)


if __name__ == "__main__":
    main()
