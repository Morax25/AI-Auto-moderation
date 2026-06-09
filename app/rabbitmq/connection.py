import pika
import os
import logging

logging.basicConfig(level=logging.INFO)

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")


def get_connection():
    try:
        logging.info(f"Connecting RabbitMQ -> {RABBITMQ_HOST}:{RABBITMQ_PORT}")
        credentials = pika.PlainCredentials(
            RABBITMQ_USER,
            RABBITMQ_PASS
        )
        params = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=credentials,
            heartbeat=60,
            blocked_connection_timeout=5,
            connection_attempts=3,
            retry_delay=2
        )
        connection = pika.BlockingConnection(params)
        logging.info("RabbitMQ connected successfully")
        return connection
    except Exception as e:
        logging.error(f"RabbitMQ connection failed: {e}")
        raise
