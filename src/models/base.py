from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    String,
    func,
    text,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )

    hash_pass: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    players: Mapped[list["Player"]] = relationship(
        back_populates="creator",
        cascade="all, delete-orphan",
    )

    teams: Mapped[list["Team"]] = relationship(
        back_populates="creator",
        cascade="all, delete-orphan",
    )

    absence_reasons: Mapped[
        list["AbsenceReason"]
    ] = relationship(
        back_populates="creator",
        cascade="all, delete-orphan",
    )


class TeamPlayer(Base):
    __tablename__ = "team_player"

    team_id: Mapped[int] = mapped_column(
        ForeignKey(
            "teams.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    player_id: Mapped[int] = mapped_column(
        ForeignKey(
            "players.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )

    created_by: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    creator: Mapped[User] = relationship(
        back_populates="players"
    )

    teams: Mapped[list["Team"]] = relationship(
        secondary="team_player",
        back_populates="players",
    )

    attendances: Mapped[
        list["TrainingAttendance"]
    ] = relationship(
        back_populates="player",
        cascade="all, delete-orphan",
    )


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )

    created_by: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    creator: Mapped[User] = relationship(
        back_populates="teams"
    )

    players: Mapped[list[Player]] = relationship(
        secondary="team_player",
        back_populates="teams",
    )

    trainings: Mapped[
        list["Training"]
    ] = relationship(
        back_populates="team",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Training(Base):
    __tablename__ = "trainings"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    team_id: Mapped[int] = mapped_column(
        ForeignKey(
            "teams.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    team: Mapped[Team] = relationship(
        back_populates="trainings"
    )

    attendances: Mapped[
        list["TrainingAttendance"]
    ] = relationship(
        back_populates="training",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class AbsenceReason(Base):
    __tablename__ = "absence_reasons"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    created_by: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # FALSE — безопасный дефолт.
    # Старые причины не получают статус "уважительная" автоматически.
    is_valid: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )

    creator: Mapped[User] = relationship(
        back_populates="absence_reasons"
    )

    attendances: Mapped[
        list["TrainingAttendance"]
    ] = relationship(
        back_populates="reason",
        passive_deletes=True,
    )


class TrainingAttendance(Base):
    """
    Существующая сущность посещаемости.

    Старый present сохраняется специально для обратной
    совместимости с существующим API.
    """

    __tablename__ = "training_attendance"

    training_id: Mapped[int] = mapped_column(
        ForeignKey(
            "trainings.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    player_id: Mapped[int] = mapped_column(
        ForeignKey(
            "players.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    present: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    reason_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "absence_reasons.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    training: Mapped[Training] = relationship(
        back_populates="attendances"
    )

    player: Mapped[Player] = relationship(
        back_populates="attendances"
    )

    reason: Mapped[
        AbsenceReason | None
    ] = relationship(
        back_populates="attendances"
    )
