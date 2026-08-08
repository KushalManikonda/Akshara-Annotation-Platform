from database.database import Base, engine
from utils.logger import logger

from database.models import (
    User,
    AudioFile,
    Annotation,
    AnnotationVersion,
    ReviewComment,
    ReviewerApproval,
    AuditLog,
)

def initialize_database():
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized!")
    
    # Auto-seed the default admin user if one doesn't exist
    from database.database import SessionLocal
    from database.enums import UserRole
    from utils.security import hash_password
    
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@akshara.com",
                password_hash=hash_password("admin123"),
                role=UserRole.ADMIN
            )
            db.add(admin)
            db.commit()
            logger.info("Default admin created successfully.")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to auto-seed admin: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    initialize_database()