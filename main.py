from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import models, schemas
from database import get_db, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# --- AUTHENTICATION (Register & Login) ---

@app.post("/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # 1. Check if email already exists
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 2. Create user
    # We manually set role=Role.LEARNER.value here.
    # The user cannot change this because 'role' is not in the 'user' input object.
    db_user = models.User(
        name=user.name,
        email=user.email,
        password=user.password,  # Raw password
        role=models.Role.LEARNER.value,  # <--- FORCED LEARNER ROLE
        avatarUrl=user.avatarUrl
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# --- LOGIN (Strict Check) ---
@app.post("/login")
def login_user(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    # Check Email + Password + Role
    db_user = db.query(models.User).filter(
        models.User.email == user_credentials.email,
        models.User.password == user_credentials.password,
        models.User.role == user_credentials.role.value
    ).first()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials or role mismatch"
        )

    return {
        "status": "success",
        "message": f"Welcome back, {db_user.name}!",
        "user_id": db_user.id,
        "role": db_user.role
    }

# --- EXISTING CRUD (Users, Vehicles, Sessions...) ---

@app.get("/users/", response_model=List[schemas.UserResponse])
def read_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()


# --- VEHICLE CRUD ---
@app.post("/vehicles/", response_model=schemas.VehicleResponse)
def create_vehicle(vehicle: schemas.VehicleCreate, db: Session = Depends(get_db)):
    db_vehicle = models.Vehicle(**vehicle.dict())
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle


@app.get("/vehicles/", response_model=List[schemas.VehicleResponse])
def read_vehicles(db: Session = Depends(get_db)):
    return db.query(models.Vehicle).all()


# --- SESSION CRUD (Complex) ---
@app.post("/sessions/", response_model=schemas.SessionResponse)
def create_session(session: schemas.SessionCreate, db: Session = Depends(get_db)):
    # 1. Extract learner IDs
    learner_ids = session.learnerIds

    # 2. Prepare data excluding learnerIds (because it's not a column, it's a relation)
    session_data = session.dict(exclude={"learnerIds"})
    new_session = models.Session(**session_data)

    # 3. Fetch Learner Objects and add to relationship
    learners = db.query(models.User).filter(models.User.id.in_(learner_ids)).all()
    new_session.learners = learners

    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    # 4. Map the response manually because of the computed names/ids lists
    return transform_session_response(new_session)


@app.get("/sessions/", response_model=List[schemas.SessionResponse])
def read_sessions(db: Session = Depends(get_db)):
    sessions = db.query(models.Session).all()
    return [transform_session_response(s) for s in sessions]


def transform_session_response(s: models.Session):
    """Helper to format Session object to match Interface requirements"""
    return schemas.SessionResponse(
        id=s.id,
        teacherId=s.teacherId,
        teacherName=s.teacher.name if s.teacher else "Unknown",
        learnerIds=[u.id for u in s.learners],
        learnerNames=[u.name for u in s.learners],
        start=s.start,
        end=s.end,
        status=s.status,
        createdAt=s.createdAt,
        cancellationReason=s.cancellationReason,
        requiresVehicle=s.requiresVehicle,
        vehicleId=s.vehicleId,
        type=s.type,
        capacity=s.capacity
    )


# --- NOTIFICATION CRUD ---
@app.post("/notifications/", response_model=schemas.NotificationResponse)
def create_notification(notif: schemas.NotificationCreate, db: Session = Depends(get_db)):
    db_notif = models.Notification(**notif.dict())
    db.add(db_notif)
    db.commit()
    db.refresh(db_notif)
    return db_notif


@app.get("/notifications/{user_id}", response_model=List[schemas.NotificationResponse])
def read_user_notifications(user_id: str, db: Session = Depends(get_db)):
    return db.query(models.Notification).filter(models.Notification.userId == user_id).all()