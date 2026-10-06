from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger, Text
from database import Base

class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, unique=True, nullable=False)
    group_name = Column(String(255))
    driver_id = Column(BigInteger, nullable=True)
    is_active = Column(Boolean, default=True)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(100))
    state = Column(String(50), default="idle")

class Logist(Base):
    __tablename__ = "logists"
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)

class Assignment(Base):
    __tablename__ = "assignments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    route_date = Column(String(50))
    depart_date = Column(String(50))
    unload_date = Column(String(50))
    local_time = Column(String(10))
    vehicle_plate = Column(String(30))
    route_name = Column(String(255))
    utc_offset = Column(Integer, default=0)
    daily = Column(Boolean, default=False)
    send_at = Column(DateTime)
    is_sent = Column(Boolean, default=False)

class ScheduledTask(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_type = Column(String(50))
    target_id = Column(BigInteger, nullable=True)
    send_at = Column(DateTime)
    text = Column(Text)
    daily = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)

class DriverDoc(Base):
    __tablename__ = "driver_docs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger)
    group_id = Column(BigInteger)
    file_id = Column(String(255))
    file_type = Column(String(20))
    sent_to_logist = Column(Boolean, default=False)

class DriverReason(Base):
    __tablename__ = "driver_reasons"
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger)
    group_id = Column(BigInteger)
    reason_text = Column(Text)

class CronMessage(Base):
    __tablename__ = "cron_messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, unique=True, nullable=False)
    message_id = Column(Integer, unique=True, nullable=False)