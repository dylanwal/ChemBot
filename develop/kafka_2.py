from confluent_kafka import Consumer

c = Consumer({
    'bootstrap.servers': 'mybroker',
    'group.id': None,
    'auto.offset.reset': 'earliest'
})

c.subscribe(['quickstart-events'])

while True:
    msg = c.poll(1.0)

    if msg is None:
        print("None")
        continue
    if msg.error():
        print("Consumer error: {}".format(msg.error()))
        continue

    print('Received message: {}'.format(msg.value().decode('utf-8')))

c.close()