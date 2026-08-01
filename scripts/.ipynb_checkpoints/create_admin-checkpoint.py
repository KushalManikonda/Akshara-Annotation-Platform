from database.database import SessionLocal
from database.models import User
from database.enums import UserRole
from utils.security import hash_password

db = SessionLocal()

admin = (
    db.query(User)
    .filter(User.role == UserRole.ADMIN)
    .first()
)

if admin:
    print("Admin already exists.")
    db.close()
    exit()

admin = User(
    username="admin",
    email="admin@akshara.com",
    password_hash=hash_password("admin123"),
    role=UserRole.ADMIN
)

db.add(admin)
db.commit()
db.close()

print("Admin created successfully.")
