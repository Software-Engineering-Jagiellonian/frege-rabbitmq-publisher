import os
import pika
import sys


def read_multiline():
    content = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        content.append(line)
    return "\n".join(content)


def app(rabbitmq_host, rabbitmq_port, queue):
    while True:
        try:
            print(f"Connecting to RabbitMQ ({rabbitmq_host}:{rabbitmq_port})...")
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port))
            channel = connection.channel()
            print("Connected")

            channel.confirm_delivery()

            channel.queue_declare(queue=queue, durable=True)

            while True:
                print("Paste JSON message and press Ctrl+D (Ctrl+Z on Windows) to send it:")
                payload = "".join(sys.stdin.readlines())
                try:
                    channel.basic_publish(exchange='',
                                      routing_key=queue,
                                      properties=pika.BasicProperties(
                                          delivery_mode=2,  # make message persistent
                                      ),
                                      body=bytes(payload, encoding='utf8'))
                    print("Message was received by RabbitMQ")
                except pika.exceptions.NackError:
                    print("Message was REJECTED by RabbitMQ (queue full?) !")

        except pika.exceptions.AMQPConnectionError as exception:
            print(f"AMQP Connection Error: {exception}")
        except KeyboardInterrupt:
            print(" Exiting...")
            try:
                connection.close()
            except NameError:
                pass
            sys.exit(0)


if __name__ == '__main__':
    try:
        rabbitmq_host = os.environ['RABBITMQ_HOST']
    except KeyError:
        print("RabbitMQ host must be provided as RABBITMQ_HOST environment var!")
        sys.exit(1)

    try:
        rabbitmq_port = int(os.environ.get('RABBITMQ_PORT', '5672'))
    except ValueError:
        print("RABBITMQ_PORT must be an integer")
        sys.exit(2)

    try:
        queue = os.environ['QUEUE']
    except KeyError:
        print("Destination queue must be provided as QUEUE environment var!")
        sys.exit(3)

    app(rabbitmq_host, rabbitmq_port, queue)
