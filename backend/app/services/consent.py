"""Parent consent (FR-03) and the consent gate: no student data is collected without participation."""

from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import decrypt_field, generate_token, keyed_hash
from app.models import Consent, ConsentLink, Guardian, Student
from app.services import messaging

NOTICE = {
    "en": {
        "title": "About the Student Diagnostic Simulator",
        "paragraphs": [
            "Your child's school is offering short game-like activities that show how your child thinks, "
            "learns and handles pressure. There are 7 sessions of about 20 minutes over 2 weeks.",
            "What we collect: answers, how long each answer takes, clicks, and (only if you allow it) features "
            "of your child's voice such as reading speed and pauses. Speech is converted to numbers on the "
            "device. Audio and video are never recorded or uploaded.",
            "What you get: a report on your child's strengths, areas to grow and simple actions for home and "
            "school. It is a screening profile, not a clinical assessment, and it never ranks your child "
            "against classmates.",
            "Who sees it: you and your child. The school sees only class-level progress unless you choose to "
            "share the individual report.",
            "Your choices: you can change these choices or withdraw at any time. Withdrawing deletes all of "
            "your child's assessment data within 7 days. Data is stored in India and kept only for the length "
            "of the school contract.",
        ],
        "choices": {
            "participate": "My child may take part",
            "voice": "Use the microphone for reading and speaking activities (only numbers are kept)",
            "share_with_school": "Share my child's individual report with the school",
        },
    },
    "hi": {
        "title": "स्टूडेंट डायग्नॉस्टिक सिम्युलेटर के बारे में",
        "paragraphs": [
            "आपके बच्चे का स्कूल खेल जैसी छोटी गतिविधियाँ दे रहा है जिनसे पता चलता है कि आपका बच्चा कैसे सोचता है, "
            "कैसे सीखता है और दबाव में कैसा करता है। 2 हफ़्तों में लगभग 20 मिनट के 7 सत्र होंगे।",
            "हम क्या एकत्र करते हैं: उत्तर, हर उत्तर में लगा समय, क्लिक, और (केवल आपकी अनुमति से) आवाज़ की कुछ "
            "विशेषताएँ जैसे पढ़ने की गति और रुकावटें। आवाज़ को डिवाइस पर ही संख्याओं में बदला जाता है। ऑडियो और "
            "वीडियो कभी रिकॉर्ड या अपलोड नहीं किए जाते।",
            "आपको क्या मिलेगा: आपके बच्चे की खूबियों, आगे बढ़ने के क्षेत्रों और घर व स्कूल के लिए आसान कदमों पर एक "
            "रिपोर्ट। यह एक स्क्रीनिंग प्रोफ़ाइल है, कोई क्लिनिकल जाँच नहीं, और यह आपके बच्चे की तुलना सहपाठियों से "
            "कभी नहीं करती।",
            "कौन देखेगा: आप और आपका बच्चा। स्कूल केवल कक्षा स्तर की प्रगति देखता है, जब तक आप व्यक्तिगत रिपोर्ट साझा करना न चुनें।",
            "आपके विकल्प: आप कभी भी ये विकल्प बदल सकते हैं या सहमति वापस ले सकते हैं। सहमति वापस लेने पर 7 दिनों के "
            "भीतर बच्चे का सारा मूल्यांकन डेटा हटा दिया जाता है। डेटा भारत में रखा जाता है और केवल स्कूल अनुबंध की "
            "अवधि तक रखा जाता है।",
        ],
        "choices": {
            "participate": "मेरा बच्चा भाग ले सकता है",
            "voice": "पढ़ने और बोलने की गतिविधियों के लिए माइक्रोफ़ोन का उपयोग करें (केवल संख्याएँ रखी जाती हैं)",
            "share_with_school": "मेरे बच्चे की व्यक्तिगत रिपोर्ट स्कूल के साथ साझा करें",
        },
    },
}


def current_consent(db: Session, student_id: str) -> Consent | None:
    return db.scalars(
        select(Consent).where(Consent.student_id == student_id).order_by(Consent.given_at.desc(), Consent.id.desc())
    ).first()


def consent_state(consent: Consent | None) -> str:
    if consent is None:
        return "pending"
    if consent.withdrawn_at is not None:
        return "withdrawn"
    return "yes" if consent.participate else "no"


def has_participation(db: Session, student_id: str) -> bool:
    return consent_state(current_consent(db, student_id)) == "yes"


def require_participation(db: Session, student_id: str) -> Consent:
    consent = current_consent(db, student_id)
    if consent_state(consent) != "yes":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "consent_required")
    assert consent is not None
    return consent


def issue_consent_link(db: Session, guardian: Guardian, school_name: str) -> str:
    token = generate_token()
    db.add(
        ConsentLink(
            guardian_id=guardian.id,
            token_hash=keyed_hash(token, scope="consent-link"),
            expires_at=datetime.now(UTC) + timedelta(days=30),
        )
    )
    link = f"{get_settings().public_web_url}/consent/{token}"
    messaging.send(
        decrypt_field(guardian.phone_enc),
        messaging.render(
            "consent_link", guardian.language, school=school_name, name=guardian.student.display_name, link=link
        ),
        kind="consent_link",
    )
    return token


def resolve_consent_link(db: Session, token: str) -> Guardian:
    link = db.scalars(
        select(ConsentLink).where(ConsentLink.token_hash == keyed_hash(token, scope="consent-link"))
    ).first()
    if link is None or link.expires_at < datetime.now(UTC):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "This consent link is invalid or has expired")
    guardian = db.get(Guardian, link.guardian_id)
    if guardian is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "This consent link is invalid or has expired")
    return guardian


def record_consent(
    db: Session,
    student: Student,
    guardian: Guardian,
    *,
    participate: bool,
    voice: bool,
    share_with_school: bool,
    language: str,
) -> Consent:
    consent = Consent(
        student_id=student.id,
        guardian_id=guardian.id,
        participate=participate,
        voice=voice and participate,
        camera=False,  # camera is a version 2 feature
        share_with_school=share_with_school and participate,
        notice_version=get_settings().notice_version,
        notice_language=language if language in NOTICE else "en",
    )
    db.add(consent)
    guardian.language = language if language in ("en", "hi") else guardian.language
    return consent
