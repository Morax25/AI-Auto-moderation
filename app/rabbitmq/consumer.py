import json
import time
import logging

from app.rabbitmq.connection import get_connection
from app.rabbitmq.config import (
    EXCHANGE_NAME,
    QUEUE_NAME,
    ROUTING_KEY
)

logging.basicConfig(level=logging.INFO)


def start_consumer(process_function):
    while True:
        try:
            connection = get_connection()
            channel = connection.channel()

            # Exchange
            channel.exchange_declare(
                exchange=EXCHANGE_NAME,
                exchange_type="direct",
                durable=True
            )
            # Queue
            channel.queue_declare(
                queue=QUEUE_NAME,
                durable=True
            )
            # Bind
            channel.queue_bind(
                exchange=EXCHANGE_NAME,
                queue=QUEUE_NAME,
                routing_key=ROUTING_KEY
            )

            channel.basic_qos(prefetch_count=1)

            def callback(ch, method, properties, body):
                try:
                    data = json.loads(body)

                    process_function(data)

                    ch.basic_ack(delivery_tag=method.delivery_tag)

                except Exception as e:
                    logging.error(f"Processing error: {e}")

                    # requeue = True for retry system
                    ch.basic_nack(
                        delivery_tag=method.delivery_tag,
                        requeue=True
                    )

            channel.basic_consume(
                queue=QUEUE_NAME,
                on_message_callback=callback
            )

            logging.info("Consumer started successfully")

        except Exception as e:
            logging.error(f"Consumer crashed: {e}")
            logging.info("Restarting consumer in 3 seconds...")
            time.sleep(3)
