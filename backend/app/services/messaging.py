"""Outbound SMS/WhatsApp messages (OTP, consent links, report links).

The provider is pluggable because the SMS/WhatsApp vendor and DLT registration are still an open
decision in the PRD. The console provider logs messages and keeps a dev-only outbox so OTPs and links
can be used locally and in tests.
"""

import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol

from app.core.config import get_settings

log = logging.getLogger("sds.messaging")


@dataclass
class Message:
    to: str
    body: str
    kind: str
    at: datetime = field(default_factory=lambda: datetime.now(UTC))


class Provider(Protocol):
    def send(self, message: Message) -> None: ...


class ConsoleProvider:
    def __init__(self) -> None:
        self.outbox: deque[Message] = deque(maxlen=500)

    def send(self, message: Message) -> None:
        self.outbox.append(message)
        log.info("[%s] to %s: %s", message.kind, message.to, message.body)


_provider: Provider | None = None


def get_provider() -> Provider:
    global _provider
    if _provider is None:
        name = get_settings().messaging_provider
        if name != "console":
            raise RuntimeError(f"Messaging provider '{name}' is not configured in this build")
        _provider = ConsoleProvider()
    return _provider


def send(to: str, body: str, kind: str) -> None:
    get_provider().send(Message(to=to, body=body, kind=kind))


def dev_outbox() -> list[Message]:
    provider = get_provider()
    return list(provider.outbox) if isinstance(provider, ConsoleProvider) else []


TEMPLATES = {
    "consent_link": {
        "en": "{school}: please review and give consent for {name} to take part in the Student Diagnostic "
        "Simulator: {link}",
        "hi": "{school}: कृपया {name} की स्टूडेंट डायग्नॉस्टिक सिम्युलेटर में भागीदारी के लिए जानकारी पढ़ें और सहमति दें: {link}",
    },
    "otp": {
        "en": "Your verification code is {code}. It expires in 5 minutes.",
        "hi": "आपका सत्यापन कोड {code} है। यह 5 मिनट में समाप्त हो जाएगा।",
    },
    "report_ready": {
        "en": "{name}'s profile report is ready: {link}",
        "hi": "{name} की प्रोफ़ाइल रिपोर्ट तैयार है: {link}",
    },
    "withdrawal_confirmed": {
        "en": "Consent withdrawn. All of {name}'s assessment data has been deleted. No further data will be collected.",
        "hi": "सहमति वापस ले ली गई है। {name} का सारा मूल्यांकन डेटा हटा दिया गया है। आगे कोई डेटा एकत्र नहीं किया जाएगा।",
    },
}


def render(kind: str, language: str, **values: str) -> str:
    templates = TEMPLATES[kind]
    return templates.get(language, templates["en"]).format(**values)
