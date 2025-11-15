import logging

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("alert_telegram")


def send_telegram_alert(message: str, chat_id: str):
    """
    Placeholder telegram alert function.
    """
    logger.warning("TELEGRAM ALERT to %s: %s", chat_id, message)
