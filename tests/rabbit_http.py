import json

from chembot.rabbitmq.rabbit_http import create_exchange, create_queue, create_binding, get, publish


def main():
    create_exchange("test_exchange")
    create_queue("test_queue")
    create_binding("test_queue", "test_exchange")

    publish("", json.dumps({"property_1": 1, "property_2": "fish"}), "test_exchange")

    reply = get("test_queue")
    print(reply)


def main2():
    from chembot.configuration import config
    from chembot.rabbitmq.messages import RabbitMessageAction
    from chembot.rabbitmq.rabbit_http_messages import write_read_create_message
    from chembot.master_controller.master_controller import MasterController
    from chembot.equipment.equipment import Equipment
    from chembot.equipment.equipment_interface import EquipmentRegistry

    name ="GUI"
    create_queue(name)
    create_binding(name, config.rabbit_exchange)

    reply = write_read_create_message(
        RabbitMessageAction(
            destination="chembot." + MasterController.name,
            source=name,
            action=MasterController.read_equipment_registry.__name__
        )
    )

    print("hi")


class Foo:
    def __init__(self):
        self.a = 1
        self.b = "2"


def main3():
    import json
    import pickle

    foo = Foo()
    foo_pickled = pickle.dumps(foo)
    foo_json = json.dumps({"pickled_foo": b"foo_pickled"})

    foo_pickled_after = json.loads(foo_json)
    foo_after = pickle.loads(foo_pickled_after["pickled_foo"])
    print(foo_after)


if __name__ == "__main__":
    main2()
