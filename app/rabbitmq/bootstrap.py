from app.rabbitmq.connection import get_connection
from app.rabbitmq.config import EXCHANGE_NAME, QUEUE_NAME, ROUTING_KEY
import logging


def setup_rabbitmq():
    conn = get_connection()
    ch = conn.channel()

    # 1. exchange
    ch.exchange_declare(
        exchange=EXCHANGE_NAME,
        exchange_type="direct",
        durable=True
    )

    # 2. queue
    ch.queue_declare(
        queue=QUEUE_NAME,
        durable=True
    )

    # 3. binding
    ch.queue_bind(
        exchange=EXCHANGE_NAME,
        queue=QUEUE_NAME,
        routing_key=ROUTING_KEY
    )

    conn.close()

    logging.info("RabbitMQ fully initialized (exchange + queue + bind)")
