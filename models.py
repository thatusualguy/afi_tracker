from datetime import datetime
from typing import List, Tuple

from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

from config import DB_FILE, TIMEZONE

engine = create_engine(f"sqlite:///{DB_FILE}", echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()


def init_db():
    Base.metadata.create_all(engine)


class ClanRating(Base):
    __tablename__ = "clan_ratings"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    total_rating = Column(Integer, nullable=False)
    members = relationship("MemberRating", back_populates="clan_rating", cascade="all, delete-orphan")


class MemberRating(Base):
    __tablename__ = "member_ratings"
    id = Column(Integer, primary_key=True)
    clan_rating_id = Column(Integer, ForeignKey("clan_ratings.id"), nullable=False)
    member_name = Column(String, nullable=False)
    rating = Column(Integer, nullable=False)
    clan_rating = relationship("ClanRating", back_populates="members")
    __table_args__ = (
        UniqueConstraint("clan_rating_id", "member_name", name="uix_member_per_rating"),
    )


def insert_rating(total_rating: int, members: List[Tuple[str, int]]):
    now = datetime.now(TIMEZONE).replace(microsecond=0)

    session = SessionLocal()
    clan_rating = ClanRating(timestamp=now, total_rating=total_rating)
    clan_rating.members = [MemberRating(member_name=name, rating=rating) for name, rating in members]
    session.add(clan_rating)
    session.commit()
    session.close()


def get_last_rating():
    session = SessionLocal()
    clan_rating = session.query(ClanRating).order_by(ClanRating.timestamp.desc()).first()
    if clan_rating:
        members = [(m.member_name, m.rating) for m in clan_rating.members]
        session.close()
        return clan_rating.timestamp, clan_rating.total_rating, members
    else:
        session.close()
        return None, None, None


def get_rating_at_time(target_time: datetime):
    session = SessionLocal()
    clan_rating = (
        session.query(ClanRating)
        .filter(ClanRating.timestamp <= target_time)
        .order_by(ClanRating.timestamp.desc())
        .first()
    )
    # print(target_time)
    # print(session.query(ClanRating)
    #       .filter(ClanRating.timestamp <= target_time))
    # print(clan_rating)
    if clan_rating:
        members = [(m.member_name, m.rating) for m in clan_rating.members]
        session.close()
        return clan_rating.timestamp, clan_rating.total_rating, members
    session.close()
    return None, None, None
