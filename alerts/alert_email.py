import logging
from typing import Dict

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("alert_email")


def send_email_alert(subject: str, message: str, recipients: Dict[str, str]):
    """
    Placeholder email alert function.
    """
    logger.warning("EMAIL ALERT: %s -> %s | %s", subject, list(recipients.values()), message)
