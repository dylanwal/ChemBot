"""
Installation
1) Open Powershell as Administrator
2) Install chocolatey (https://chocolatey.org/install)
3) Install RabbitMQ `choco install rabbitmq`
4) Server starts up automatically on install

RabbitMQ
    # Navigate to location of server files
    'cd C:\Program Files\RabbitMQ Server\rabbitmq_server-3.11.13\sbin'  # version may be different

    # start server
    `.\rabbitmq-server.bat -detached`

    # stop server
    `.\rabbitmqctl.bat stop`

    # check server status
    `.\rabbitmqctl.bat status`


# checking server
http://localhost:15672/
Username: guest
Password: guest

"""
import sys
import os

import pika


def prod():
    connection = pika.BlockingConnection(pika.ConnectionParameters('5672'))
    channel = connection.channel()

    channel.queue_declare(queue='hello')

    channel.basic_publish(exchange='',
                          routing_key='hello',
                          body='Hello World!')
    print(" [x] Sent 'Hello World!'")

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
        cons()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
