from datetime import datetime

from sqlalchemy.orm import Session

from database.database import SessionLocal
from database.models import AudioFile, Annotation
from database.enums import AnnotationState, AudioStatus

from utils.rsml.tokenizer import tokenize
from utils.rsml.parser import RSMLParser
from utils.rsml.validator import RSMLValidator
from utils.rsml.normalizer import RSMLNormalizer

parser = RSMLParser()
validator = RSMLValidator()
normalizer = RSMLNormalizer()

def get_db() -> Session:
    return SessionLocal()


def get_tasks(annotator_id):

    db = get_db()

    try:
        return (
            db.query(AudioFile)
            .filter(AudioFile.assigned_to == annotator_id)
            .all()
        )

    finally:
        db.close()


def get_annotation(audio_id, annotator_id):

    db = get_db()

    try:
        annotation = (
            db.query(Annotation)
            .filter(
                Annotation.audio_id == audio_id,
                Annotation.annotator_id == annotator_id
            )
            .first()
        )

        if not annotation:

            annotation = Annotation(
                audio_id=audio_id,
                annotator_id=annotator_id
            )

            db.add(annotation)
            db.commit()
            db.refresh(annotation)

        return annotation

    finally:
        db.close()


def save_annotation(annotation_id, transcript, rsml):

    db = get_db()

    try:

        annotation = (
            db.query(Annotation)
            .filter(Annotation.id == annotation_id)
            .first()
        )

        if not annotation:
            return False

        annotation.transcript = transcript
        annotation.rsml_content = rsml
        annotation.state = AnnotationState.DRAFT

        db.commit()

        return True

    finally:
        db.close()


def submit_annotation(annotation_id):

    db = get_db()

    try:

        annotation = (
            db.query(Annotation)
            .filter(Annotation.id == annotation_id)
            .first()
        )

        if not annotation:
            return False

        annotation.state = AnnotationState.SUBMITTED
        annotation.submitted_at = datetime.utcnow()

        audio = (
            db.query(AudioFile)
            .filter(AudioFile.id == annotation.audio_id)
            .first()
        )

        audio.status = AudioStatus.SUBMITTED

        db.commit()

        return True

    finally:
        db.close()

def process_transcript(transcript: str):
    """
    Process an RSML transcript and return all derived outputs.

    Returns:
        {
            "tokens": [...],
            "ast": [...],
            "messages": [...],
            "normalized": "..."
        }
    """

    tokens = tokenize(transcript)

    ast = parser.parse(tokens)

    messages = validator.validate(ast)

    normalized = normalizer.normalize(ast)

    return {
        "tokens": tokens,
        "ast": ast,
        "messages": messages,
        "normalized": normalized,
    }