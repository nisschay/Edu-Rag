"""
Topic service for topic-related database operations.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.topic import Topic
from app.schemas.topic import TopicCreate


def get_topic_by_id(db: Session, topic_id: int) -> Topic | None:
    """
    Get a topic by ID.
    
    Args:
        db: Database session.
        topic_id: Topic ID to look up.
        
    Returns:
        Topic if found, None otherwise.
    """
    return db.get(Topic, topic_id)


def get_topic_for_unit(
    db: Session,
    topic_id: int,
    unit_id: int,
) -> Topic | None:
    """
    Get a topic by ID, ensuring it belongs to the specified unit.
    
    Args:
        db: Database session.
        topic_id: Topic ID to look up.
        unit_id: Unit ID that must own the topic.
        
    Returns:
        Topic if found and belongs to unit, None otherwise.
    """
    stmt = select(Topic).where(
        Topic.id == topic_id,
        Topic.unit_id == unit_id,
    )
    return db.scalar(stmt)


def list_topics_for_unit(db: Session, unit_id: int) -> list[Topic]:
    """
    List all topics for a unit.
    
    Args:
        db: Database session.
        unit_id: Unit ID to list topics for.
        
    Returns:
        List of topics ordered by creation time.
    """
    stmt = (
        select(Topic)
        .where(Topic.unit_id == unit_id)
        .order_by(Topic.created_at)
    )
    return list(db.scalars(stmt).all())


def create_topic(
    db: Session,
    topic_in: TopicCreate,
    unit_id: int,
) -> Topic:
    """
    Create a new topic for a unit.
    
    Args:
        db: Database session.
        topic_in: Topic creation data.
        unit_id: ID of the parent unit.
        
    Returns:
        Created topic instance.
    """
    topic = Topic(
        title=topic_in.title,
        unit_id=unit_id,
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic
