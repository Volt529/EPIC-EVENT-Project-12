from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    ForeignKey, DateTime, Text
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False)  # 'gestion', 'commercial', 'support'
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    clients = relationship("Client", back_populates="sales_contact")
    contracts = relationship("Contract", back_populates="sales_contact")
    supported_events = relationship("Event", back_populates="support_contact")


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20))
    company = Column(String(100))
    creation_date = Column(DateTime(timezone=True), server_default=func.now())
    last_update = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    sales_contact_id = Column(Integer, ForeignKey("users.id"))

    # Relations
    sales_contact = relationship("User", back_populates="clients")
    contracts = relationship("Contract", back_populates="client")


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    sales_contact_id = Column(Integer, ForeignKey("users.id"))
    total_amount = Column(Float, nullable=False)
    remaining_amount = Column(Float, nullable=False)
    creation_date = Column(DateTime(timezone=True), server_default=func.now())
    is_signed = Column(Boolean, default=False)

    # Relations
    client = relationship("Client", back_populates="contracts")
    sales_contact = relationship("User", back_populates="contracts")
    events = relationship("Event", back_populates="contract")


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    event_name = Column(String(100), nullable=False)
    contract_id = Column(Integer, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    support_contact_id = Column(Integer, ForeignKey("users.id"))
    location = Column(Text)
    attendees = Column(Integer)
    notes = Column(Text)

    # Relations
    contract = relationship("Contract", back_populates="events")
    support_contact = relationship("User", back_populates="supported_events")