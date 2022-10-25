"""

    # Navigate to location of server files
    'cd C:\Program Files\RabbitMQ Server\rabbitmq_server-3.10.6\sbin'

    # start server
    `.\rabbitmq-server.bat -detached`

    # stop server
    `.\rabbitmqctl.bat stop`

    # check server status
    `.\rabbitmqctl.bat status`

"""
import sys
import os

import pika


def prod():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='hello')

    for i in range(100):
        channel.basic_publish(exchange='',
                              routing_key='hello',
                              body=f'{i} Hello World!')
        print(i)

    connection.close()


def cons():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='hello')

    def callback(ch, method, properties, body):
        print(" [x] Received %r" % body)

    channel.basic_consume(queue='hello',
                          auto_ack=True,
                          on_message_callback=callback)
    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()


if __name__ == "__main__":
    try:
        prod()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
