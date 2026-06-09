from app.rabbitmq.connection import get_connection
from app.rabbitmq.config import EXCHANGE_NAME
import logging


def setup_exchange():
    connection = get_connection()
    channel = connection.channel()

    channel.exchange_declare(
        exchange=EXCHANGE_NAME,
        exchange_type="direct",
        durable=True
    )

    logging.info(f"Exchange declared: {EXCHANGE_NAME}")

    connection.close()
