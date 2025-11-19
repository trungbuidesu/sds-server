from typing import List, Optional
from xmlrpc.client import boolean

from pydantic import BaseModel, EmailStr
from datetime import datetime
from models import Role, VehicleStatus, SessionStatus, SessionType

# --- USER SCHEMAS ---
# Base: Shared fields (Name, Email, Avatar)
class UserBase(BaseModel):
    name: str
    email: EmailStr
    avatarUrl: Optional[str] = None

# Input: Register (Password added, NO ROLE here)
class UserCreate(UserBase):
    password: str

# Input: Login (Role is required here for the check)
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    role: Role

# Output: Response (Includes ID and Role)
class UserResponse(UserBase):
    id: str
    role: Role

    class Config:
        from_attributes = True

# --- VEHICLE SCHEMAS ---
class VehicleBase(BaseModel):
    name: str
    plate: str
    status: VehicleStatus = VehicleStatus.ACTIVE

class VehicleCreate(VehicleBase):
    pass

class VehicleResponse(VehicleBase):
    id: str
    class Config:
        from_attributes = True

# --- SESSION SCHEMAS ---
class SessionCreate(BaseModel):
    teacherId: str
    learnerIds: List[str] # User sends IDs
    start: datetime
    end: datetime
    requiresVehicle: boolean
    vehicleId: Optional[str] = None
    type: SessionType
    capacity: Optional[int] = None

class SessionResponse(BaseModel):
    id: str
    teacherId: str
    teacherName: str # Computed field
    learnerIds: List[str] # Computed field
    learnerNames: List[str] # Computed field
    start: datetime
    end: datetime
    status: SessionStatus
    createdAt: datetime
    cancellationReason: Optional[str]
    requiresVehicle: bool
    vehicleId: Optional[str]
    type: SessionType
    capacity: Optional[int]

    class Config:
        from_attributes = True

# --- NOTIFICATION SCHEMAS ---
class NotificationCreate(BaseModel):
    userId: str
    message: str

class NotificationResponse(BaseModel):
    id: str
    userId: str
    message: str
    read: bool
    timestamp: datetime
    class Config:
        from_attributes = True