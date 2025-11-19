import uuid
import enum
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Table, Enum as SAEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


# --- ENUMS ---
class Role(str, enum.Enum):
    LEARNER = "learner"
    TEACHER = "teacher"
    ADMIN = "admin"


class VehicleStatus(str, enum.Enum):
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    RETIRED = "retired"


class SessionStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SessionType(str, enum.Enum):
    THEORY = "theory"
    PRACTICAL = "practical"


# --- ASSOCIATION TABLE (For Many-to-Many: Session <-> Learners) ---
session_learners = Table(
    "session_learners",
    Base.metadata,
    Column("session_id", String, ForeignKey("sessions.id")),
    Column("user_id", String, ForeignKey("users.id"))
)


# --- MODELS ---

class User(Base):
    __tablename__ = "users"
    # We use UUIDs as strings for IDs
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)  # Raw password per request
    role = Column(String, default=Role.LEARNER.value)
    avatarUrl = Column(String, nullable=True)

    # Relationships
    sessions_teaching = relationship("Session", back_populates="teacher")
    notifications = relationship("Notification", back_populates="user")
    # Many-to-Many relationship for sessions attended
    sessions_attending = relationship("Session", secondary=session_learners, back_populates="learners")


class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String)
    plate = Column(String, unique=True)
    status = Column(String, default=VehicleStatus.ACTIVE.value)


class Session(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Teacher Info
    teacherId = Column(String, ForeignKey("users.id"))
    teacher = relationship("User", back_populates="sessions_teaching")
    # Note: We don't store teacherName in DB, we fetch it via relationship to keep data normalized

    # Many-to-Many relationship defined in User model
    learners = relationship("User", secondary=session_learners, back_populates="sessions_attending")

    start = Column(DateTime)
    end = Column(DateTime)
    status = Column(String, default=SessionStatus.SCHEDULED.value)
    createdAt = Column(DateTime, default=datetime.now)
    cancellationReason = Column(String, nullable=True)

    requiresVehicle = Column(Boolean, default=False)
    vehicleId = Column(String, ForeignKey("vehicles.id"), nullable=True)
    type = Column(String, default=SessionType.THEORY.value)
    capacity = Column(Integer, nullable=True)


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    userId = Column(String, ForeignKey("users.id"))
    message = Column(String)
    read = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="notifications")