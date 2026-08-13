from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.database import Base, TimestampMixin


def new_id() -> str:
    return str(uuid.uuid4())


class Account(TimestampMixin, Base):
    __tablename__ = "Account"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    display_name: Mapped[str] = mapped_column("displayName", String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    avatar_url: Mapped[str | None] = mapped_column("avatarUrl", String(500), nullable=True)


class Meeting(TimestampMixin, Base):
    __tablename__ = "Meeting"
    __table_args__ = (
        CheckConstraint("durationInSeconds >= 0", name="meeting_duration_non_negative"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_account_id: Mapped[str] = mapped_column(
        "ownerAccountId", ForeignKey("Account.id"), index=True
    )
    title: Mapped[str] = mapped_column(String(200), index=True)
    meeting_at_utc: Mapped[datetime] = mapped_column(
        "meetingAtUtc", DateTime(timezone=True), index=True
    )
    duration_in_seconds: Mapped[int] = mapped_column("durationInSeconds", Integer)
    source_type: Mapped[str] = mapped_column("sourceType", String(30), default="uploaded")
    media_url: Mapped[str | None] = mapped_column("mediaUrl", String(500), nullable=True)
    deleted_at_utc: Mapped[datetime | None] = mapped_column(
        "deletedAtUtc", DateTime(timezone=True), nullable=True, index=True
    )

    owner: Mapped[Account] = relationship(lazy="joined")
    participants: Mapped[list[MeetingParticipant]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan", lazy="selectin"
    )
    transcript_segments: Mapped[list[TranscriptSegment]] = relationship(
        back_populates="meeting",
        cascade="all, delete-orphan",
        order_by="TranscriptSegment.sequence_number",
        lazy="selectin",
    )
    summary: Mapped[MeetingSummary | None] = relationship(
        back_populates="meeting", cascade="all, delete-orphan", uselist=False, lazy="selectin"
    )
    chapters: Mapped[list[Chapter]] = relationship(
        back_populates="meeting",
        cascade="all, delete-orphan",
        order_by="Chapter.start_in_seconds",
        lazy="selectin",
    )
    action_items: Mapped[list[ActionItem]] = relationship(
        back_populates="meeting",
        cascade="all, delete-orphan",
        order_by="ActionItem.created_at_utc",
        lazy="selectin",
    )


class Participant(TimestampMixin, Base):
    __tablename__ = "Participant"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(120), index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    avatar_color: Mapped[str] = mapped_column("avatarColor", String(20), default="#5865F2")


class MeetingParticipant(Base):
    __tablename__ = "MeetingParticipant"
    __table_args__ = (UniqueConstraint("meetingId", "participantId"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    meeting_id: Mapped[str] = mapped_column(
        "meetingId", ForeignKey("Meeting.id", ondelete="CASCADE"), index=True
    )
    participant_id: Mapped[str] = mapped_column(
        "participantId", ForeignKey("Participant.id"), index=True
    )
    is_host: Mapped[bool] = mapped_column("isHost", default=False)

    meeting: Mapped[Meeting] = relationship(back_populates="participants")
    participant: Mapped[Participant] = relationship(lazy="joined")


class TranscriptSegment(TimestampMixin, Base):
    __tablename__ = "TranscriptSegment"
    __table_args__ = (
        UniqueConstraint("meetingId", "sequenceNumber"),
        CheckConstraint("startInSeconds >= 0", name="segment_start_non_negative"),
        CheckConstraint("endInSeconds >= startInSeconds", name="segment_end_after_start"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    meeting_id: Mapped[str] = mapped_column(
        "meetingId", ForeignKey("Meeting.id", ondelete="CASCADE"), index=True
    )
    speaker_participant_id: Mapped[str | None] = mapped_column(
        "speakerParticipantId", ForeignKey("Participant.id"), nullable=True, index=True
    )
    sequence_number: Mapped[int] = mapped_column("sequenceNumber", Integer)
    start_in_seconds: Mapped[float] = mapped_column("startInSeconds", Float)
    end_in_seconds: Mapped[float] = mapped_column("endInSeconds", Float)
    text: Mapped[str] = mapped_column(Text)

    meeting: Mapped[Meeting] = relationship(back_populates="transcript_segments")
    speaker: Mapped[Participant | None] = relationship(lazy="joined")


class MeetingSummary(TimestampMixin, Base):
    __tablename__ = "MeetingSummary"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    meeting_id: Mapped[str] = mapped_column(
        "meetingId", ForeignKey("Meeting.id", ondelete="CASCADE"), unique=True, index=True
    )
    overview: Mapped[str] = mapped_column(Text)

    meeting: Mapped[Meeting] = relationship(back_populates="summary")
    key_points: Mapped[list[SummaryKeyPoint]] = relationship(
        back_populates="summary",
        cascade="all, delete-orphan",
        order_by="SummaryKeyPoint.sequence_number",
        lazy="selectin",
    )


class SummaryKeyPoint(Base):
    __tablename__ = "SummaryKeyPoint"
    __table_args__ = (UniqueConstraint("summaryId", "sequenceNumber"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    summary_id: Mapped[str] = mapped_column(
        "summaryId", ForeignKey("MeetingSummary.id", ondelete="CASCADE"), index=True
    )
    sequence_number: Mapped[int] = mapped_column("sequenceNumber", Integer)
    text: Mapped[str] = mapped_column(Text)

    summary: Mapped[MeetingSummary] = relationship(back_populates="key_points")


class Chapter(Base):
    __tablename__ = "Chapter"
    __table_args__ = (CheckConstraint("startInSeconds >= 0", name="chapter_start_non_negative"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    meeting_id: Mapped[str] = mapped_column(
        "meetingId", ForeignKey("Meeting.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(160))
    start_in_seconds: Mapped[float] = mapped_column("startInSeconds", Float)

    meeting: Mapped[Meeting] = relationship(back_populates="chapters")


class ActionItem(TimestampMixin, Base):
    __tablename__ = "ActionItem"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    meeting_id: Mapped[str] = mapped_column(
        "meetingId", ForeignKey("Meeting.id", ondelete="CASCADE"), index=True
    )
    assignee_participant_id: Mapped[str | None] = mapped_column(
        "assigneeParticipantId", ForeignKey("Participant.id"), nullable=True, index=True
    )
    description: Mapped[str] = mapped_column(Text)
    is_completed: Mapped[bool] = mapped_column("isCompleted", default=False, index=True)
    due_at_utc: Mapped[datetime | None] = mapped_column(
        "dueAtUtc", DateTime(timezone=True), nullable=True
    )

    meeting: Mapped[Meeting] = relationship(back_populates="action_items")
    assignee: Mapped[Participant | None] = relationship(lazy="joined")
