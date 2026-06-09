import json
import pika
import logging

from app.rabbitmq.connection import get_connection
from app.rabbitmq.config import EXCHANGE_NAME, ROUTING_KEY


def publish_moderation_job(payload: dict):
    connection = get_connection()
    channel = connection.channel()

    try:
        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=ROUTING_KEY,
            body=json.dumps(payload),
            properties=pika.BasicProperties(
                delivery_mode=2
            )
        )

        logging.info("Message published")

    finally:
        connection.close()
