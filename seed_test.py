from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User
from app.models.subject import Subject
from app.models.unit import Unit
from app.models.topic import Topic

def seed():
    db = SessionLocal()
    try:
        # Create user
        user = User(id=1, email="test@example.com")
        db.merge(user)
        
        # Create subject
        subject = Subject(id=1, name="Test Subject", user_id=1)
        db.merge(subject)
        
        # Create unit
        unit = Unit(id=1, title="Test Unit", unit_number=1, subject_id=1)
        db.merge(unit)
        
        # Create topic
        topic = Topic(id=1, title="Test Topic", unit_id=1)
        db.merge(topic)
        
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
    print("Seeded successfully")
