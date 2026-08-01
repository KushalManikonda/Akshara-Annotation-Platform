from enum import Enum

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    ANNOTATOR = "ANNOTATOR"
    REVIEWER = "REVIEWER"


class AudioStatus(str, Enum):
    UNASSIGNED = "UNASSIGNED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    REVIEWED = "REVIEWED"


class AnnotationState(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    RETURNED = "RETURNED"
    APPROVED = "APPROVED"


class ReviewDecision(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ValidationState(str, Enum):
    VALID = "VALID"
    HAS_ERRORS = "HAS_ERRORS"
    HAS_WARNINGS = "HAS_WARNINGS"


class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class AuditAction(str, Enum):
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    SUBMIT = "SUBMIT"
    RETURN = "RETURN"
    APPROVE = "APPROVE"
    REJECT = "REJECT"