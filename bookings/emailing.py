import logging
import threading

from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def _send(kwargs):
    try:
        send_mail(**kwargs)
    except Exception:
        logger.exception("Email failed: %s", kwargs.get('subject'))


def send_email_async(**kwargs):
    """Send an email without making the customer wait for it."""
    threading.Thread(target=_send, args=(kwargs,), daemon=True).start()