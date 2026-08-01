from datetime import datetime

from sqlalchemy.orm import Session

from database.database import SessionLocal
from database.models import (
    Annotation,
    ReviewComment,
    ReviewerApproval,
    AudioFile
)

from database.enums import (
    AnnotationState,
    ApprovalStatus,
    AudioStatus
)


def get_db() -> Session:
    return SessionLocal()


def get_submitted_annotations():

    db = get_db()

    try:
        return (
            db.query(Annotation)
            .filter(
                Annotation.state == AnnotationState.SUBMITTED
            )
            .all()
        )

    finally:
        db.close()


def add_comment(annotation_id, reviewer_id, comment):

    db = get_db()

    try:

        annotation = (
            db.query(Annotation)
            .filter(Annotation.id == annotation_id)
            .first()
        )

        version = len(annotation.versions)

        review = ReviewComment(
            annotation_id=annotation.id,
            reviewer_id=reviewer_id,
            version_commented=version,
            comment=comment,
            is_return_reason=True
        )

        db.add(review)

        annotation.state = AnnotationState.DRAFT

        audio = (
            db.query(AudioFile)
            .filter(AudioFile.id == annotation.audio_id)
            .first()
        )

        audio.status = AudioStatus.ASSIGNED

        db.commit()

        return True

    finally:
        db.close()


def approve(annotation_id, reviewer_id):

    db = get_db()

    try:

        annotation = (
            db.query(Annotation)
            .filter(Annotation.id == annotation_id)
            .first()
        )

        version = len(annotation.versions)

        approval = ReviewerApproval(
            annotation_id=annotation.id,
            reviewer_id=reviewer_id,
            version_approved=version,
            status=ApprovalStatus.APPROVED
        )

        db.add(approval)

        annotation.state = AnnotationState.APPROVED

        audio = (
            db.query(AudioFile)
            .filter(AudioFile.id == annotation.audio_id)
            .first()
        )

        audio.status = AudioStatus.COMPLETED

        db.commit()

        return True

    finally:
        db.close()