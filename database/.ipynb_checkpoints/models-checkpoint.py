from uuid import uuid4
from datetime import datetime
from database.database import Base
from sqlalchemy.orm import relationship

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Text,
    Integer,
    Boolean,
)

from database.enums import (
    UserRole,
    AudioStatus,
    AnnotationState,
    ApprovalStatus,
    AuditAction,
)

class User(Base):
    __tablename__ = "users"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid4())
    )

    username = Column(
        String,
        unique=True,
        nullable=False
    )

    email = Column(
        String,
        unique=True,
        nullable=False
    )

    password_hash = Column(
        String,
        nullable=False
    )

    role = Column(
        Enum(UserRole),
        nullable=False,
        default=UserRole.ANNOTATOR
    )

    is_active = Column(
        Boolean,
        default=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    last_login = Column(
        DateTime,
        nullable=True
    )

    last_seen = Column(
        DateTime,
        nullable=True
    )

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid4())
    )
    
    name = Column(
        String,
        nullable=False
    )

    zip_filename = Column(
        String,
        nullable=False
    )

    language = Column(
        String,
        nullable=False
    )

    uploaded_by = Column(
        String,
        ForeignKey("users.id"),
        nullable=False
    )

    total_files = Column(
        Integer,
        default=0,
        nullable=False
    )

    total_duration = Column(
        Float,
        default=0.0,
        nullable=False
    )

    uploaded_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    uploader = relationship(
        "User"
    )

    total_size = Column(
        Float,
        default=0.0,
        nullable=False
    )
    
class AudioFile(Base):
    __tablename__ = "audio_files"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid4())
    )

    dataset_id = Column(
        String,
        ForeignKey("datasets.id"),
        nullable=False
    )

    dataset = relationship(
        "Dataset",
        backref="audio_files"
    )
    
    filename = Column(
        String,
        nullable=False
    )

    original_filename = Column(
        String,
        nullable=False
    )

    file_path = Column(
        String,
        nullable=False
    )

    language = Column(
        String,
        nullable=False
    )

    # Will be computed later during upload
    duration = Column(
        Float,
        nullable=True,
        default=0.0
    )

    status = Column(
        Enum(AudioStatus),
        nullable=False,
        default=AudioStatus.UNASSIGNED
    )

    # Will be filled automatically from the logged-in admin later
    uploaded_by = Column(
        String,
        ForeignKey("users.id"),
        nullable=True
    )

    assigned_to = Column(
        String,
        ForeignKey("users.id"),
        nullable=True
    )

    uploaded_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    uploader = relationship(
        "User",
        foreign_keys=[uploaded_by]
    )

    assignee = relationship(
        "User",
        foreign_keys=[assigned_to]
    )

class Annotation(Base):
    __tablename__ = "annotations"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid4())
    )

    audio_id = Column(
        String,
        ForeignKey("audio_files.id"),
        nullable=False
    )

    annotator_id = Column(
        String,
        ForeignKey("users.id"),
        nullable=False
    )

    transcript = Column(
        Text,
        nullable=True
    )

    rsml_content = Column(
        Text,
        nullable=True
    )

    state = Column(
        Enum(AnnotationState),
        default=AnnotationState.DRAFT,
        nullable=False
    )

    submitted_at = Column(
        DateTime,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    audio = relationship(
        "AudioFile",
        backref="annotation"
    )

    annotator = relationship(
        "User",
        foreign_keys=[annotator_id]
    )

class AnnotationVersion(Base):
    __tablename__ = "annotation_versions"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid4())
    )

    annotation_id = Column(
        String,
        ForeignKey("annotations.id"),
        nullable=False
    )

    version_number = Column(
        Integer,
        nullable=False
    )

    transcript_snapshot = Column(
        Text,
        nullable=True
    )

    rsml_snapshot = Column(
        Text,
        nullable=True
    )

    submitted_by = Column(
        String,
        ForeignKey("users.id"),
        nullable=False
    )

    submitted_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    annotation = relationship(
        "Annotation",
        backref="versions"
    )

    submitter = relationship(
        "User"
    )

class ReviewComment(Base):
    __tablename__ = "review_comments"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid4())
    )

    annotation_id = Column(
        String,
        ForeignKey("annotations.id"),
        nullable=False
    )

    reviewer_id = Column(
        String,
        ForeignKey("users.id"),
        nullable=False
    )

    version_commented = Column(
        Integer,
        nullable=False
    )

    span_start = Column(
        Integer,
        nullable=True
    )

    span_end = Column(
        Integer,
        nullable=True
    )

    comment = Column(
        Text,
        nullable=False
    )

    is_return_reason = Column(
        Boolean,
        default=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    annotation = relationship(
        "Annotation",
        backref="comments"
    )

    reviewer = relationship(
        "User"
    )

class ReviewerApproval(Base):
    __tablename__ = "reviewer_approvals"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid4())
    )

    annotation_id = Column(
        String,
        ForeignKey("annotations.id"),
        nullable=False
    )

    reviewer_id = Column(
        String,
        ForeignKey("users.id"),
        nullable=False
    )

    version_approved = Column(
        Integer,
        nullable=False
    )

    status = Column(
        Enum(ApprovalStatus),
        default=ApprovalStatus.PENDING,
        nullable=False
    )

    is_valid = Column(
        Boolean,
        default=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    annotation = relationship(
        "Annotation",
        backref="approvals"
    )

    reviewer = relationship(
        "User"
    )

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid4())
    )

    user_id = Column(
        String,
        ForeignKey("users.id"),
        nullable=False
    )

    annotation_id = Column(
        String,
        ForeignKey("annotations.id"),
        nullable=True
    )

    action = Column(
        Enum(AuditAction),
        nullable=False
    )

    details = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    user = relationship(
        "User"
    )

    annotation = relationship(
        "Annotation"
    )

