"""
Database models and operations for the AFI Tracker.

This module defines the SQLAlchemy models for the database and provides
functions for common database operations.
"""

import logging
from contextlib import contextmanager
from datetime import datetime
from typing import List, Tuple, Optional, Generator

from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, select, desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session

from config import DB_FILE, TIMEZONE

logger = logging.getLogger(__name__)

# Create SQLAlchemy engine and session factory
engine = create_engine(f"sqlite:///{DB_FILE}", echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    
    Yields:
        SQLAlchemy Session object
        
    Raises:
        SQLAlchemyError: If a database error occurs
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        session.close()


def init_db() -> None:
    """
    Initialize the database by creating all tables.
    """
    try:
        Base.metadata.create_all(engine)
        logger.info("Database initialized successfully")
    except SQLAlchemyError as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


class ClanRating(Base):
    """
    Model representing a clan's rating at a specific point in time.
    """
    __tablename__ = "clan_ratings"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    total_rating = Column(Integer, nullable=False)
    members = relationship("MemberRating", back_populates="clan_rating", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ClanRating(timestamp={self.timestamp}, total_rating={self.total_rating})>"


class MemberRating(Base):
    """
    Model representing a member's rating within a clan rating snapshot.
    """
    __tablename__ = "member_ratings"

    id = Column(Integer, primary_key=True)
    clan_rating_id = Column(Integer, ForeignKey("clan_ratings.id"), nullable=False)
    member_name = Column(String, nullable=False)
    rating = Column(Integer, nullable=False)
    clan_rating = relationship("ClanRating", back_populates="members")

    __table_args__ = (
        UniqueConstraint("clan_rating_id", "member_name", name="uix_member_per_rating"),
    )

    def __repr__(self) -> str:
        return f"<MemberRating(member_name={self.member_name}, rating={self.rating})>"


def insert_rating(total_rating: int, members: List[Tuple[str, int]]) -> None:
    """
    Insert a new clan rating record with member ratings.
    
    Args:
        total_rating: The total rating of the clan
        members: List of (member_name, rating) tuples
        
    Raises:
        SQLAlchemyError: If a database error occurs
    """
    now = datetime.now(TIMEZONE).replace(microsecond=0)

    with get_db_session() as session:
        clan_rating = ClanRating(timestamp=now, total_rating=total_rating)
        clan_rating.members = [MemberRating(member_name=name, rating=rating) for name, rating in members]
        session.add(clan_rating)
        logger.info(f"Inserted new clan rating: {total_rating} with {len(members)} members")


def get_last_rating() -> Tuple[Optional[datetime], Optional[int], Optional[List[Tuple[str, int]]]]:
    """
    Get the most recent clan rating.
    
    Returns:
        Tuple of (timestamp, total_rating, members) where members is a list of (member_name, rating) tuples.
        If no ratings exist, returns (None, None, None).
        
    Raises:
        SQLAlchemyError: If a database error occurs
    """
    with get_db_session() as session:
        stmt = select(ClanRating).order_by(desc(ClanRating.timestamp)).limit(1)
        clan_rating = session.execute(stmt).scalars().first()

        if clan_rating:
            members = [(m.member_name, m.rating) for m in clan_rating.members]
            logger.debug(f"Retrieved last rating from {clan_rating.timestamp}")
            return clan_rating.timestamp, clan_rating.total_rating, members

        logger.warning("No clan ratings found in database")
        return None, None, None


def get_rating_at_time(target_time: datetime) -> Tuple[
    Optional[datetime], Optional[int], Optional[List[Tuple[str, int]]]]:
    """
    Get the clan rating closest to but not after the specified time.
    
    Args:
        target_time: The target datetime
        
    Returns:
        Tuple of (timestamp, total_rating, members) where members is a list of (member_name, rating) tuples.
        If no ratings exist before the target time, returns (None, None, None).
        
    Raises:
        SQLAlchemyError: If a database error occurs
    """
    with get_db_session() as session:
        stmt = (
            select(ClanRating)
            .filter(ClanRating.timestamp <= target_time)
            .order_by(desc(ClanRating.timestamp))
            .limit(1)
        )
        clan_rating = session.execute(stmt).scalars().first()

        if clan_rating:
            members = [(m.member_name, m.rating) for m in clan_rating.members]
            logger.debug(f"Retrieved rating at {clan_rating.timestamp} for target time {target_time}")
            return clan_rating.timestamp, clan_rating.total_rating, members

        logger.warning(f"No clan ratings found before {target_time}")
        return None, None, None
