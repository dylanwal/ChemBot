from time import sleep
from json import dumps
from kafka import KafkaProducer, KafkaConsumer
import logging
logging.basicConfig(level=logging.INFO)

# producer = KafkaProducer(bootstrap_servers=['localhost:9092'])
producer = KafkaProducer(bootstrap_servers='localhost:9092')
producer.send('Jim_Topic', b'Message from PyCharm')
producer.send('Jim_Topic', key=b'message-two', value=b'This is Kafka-Python')
producer.flush()

# consumer = KafkaConsumer('quickstart-events', bootstrap_servers=['localhost:9092'])
#
#
# for i in range(1000):
#     # producer.send('quickstart-events', value="data".encode())
#     sleep(2)
#     print("C: ", consumer.poll())

