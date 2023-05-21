
import chembot

gui = chembot.GUI()
gui.activate()  # blocking

# import chembot.rabbitmq.REST_rabbit as rest
# from chembot.rabbitmq.messages import RabbitMessageAction
#
# gui_queue = rest.create_queue()
#
#
# r = rest.write_message(RabbitMessageAction("master_controller", "gui", "read_equipment_status"))
