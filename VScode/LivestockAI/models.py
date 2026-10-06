from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DECIMAL,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    TIMESTAMP,
    UniqueConstraint,
    checkconstraint,
)
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class UserRole(str, Enum):
    Admin = "Admin"
    Seller = "Seller"
    Buyer = "Buyer"


class UserStatus(str, Enum):
    Pending = "Pending"
    Active = "Active"
    Suspended = "Suspended"
    Banned = "Banned"


class AnimalType(str, Enum):
    Cow = "Cow"
    Buffalo = "Buffalo"
    Goat = "Goat"
    Sheep = "Sheep"
    Horse = "Horse"
    Dog = "Dog"
    Cat = "Cat"
    Camel = "Camel"
    Rabbit = "Rabbit"
    Poultry = "Poultry"


class GenderType(str, Enum):
    Male = "Male"
    Female = "Female"
    Other = "Other"


class AvailabilityStatus(str, Enum):
    Available = "Available"
    Reserved = "Reserved"
    Sold = "Sold"
    Pending = "Pending"


class SeverityType(str, Enum):
    Low = "Low"
    Medium = "Medium"
    High = "High"
    Critical = "Critical"


class ReportType(str, Enum):
    Seller = "Seller"
    Animal = "Animal"
    Fraud = "Fraud"
    Spam = "Spam"
    Fake_Images = "Fake Images"
    Animal_Abuse = "Animal Abuse"


class ReportStatus(str, Enum):
    Pending = "Pending"
    Reviewed = "Reviewed"
    Approved = "Approved"
    Rejected = "Rejected"


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    phone = Column(String(30), nullable=True)
    password_hash = Column(String(255), nullable=False)
    profile_image = Column(String(500), nullable=True)
    role = Column(Enum(UserRole), nullable=False)
    status = Column(Enum(UserStatus), nullable=False, default=UserStatus.Pending)
    email_verified = Column(TINYINT(1), nullable=False, default=0)
    otp_verified = Column(TINYINT(1), nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    seller_profile = relationship("SellerProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    buyer_profile = relationship("BuyerProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    animals = relationship("Animal", back_populates="seller", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="buyer", cascade="all, delete-orphan")
    chats_as_buyer = relationship("Chat", foreign_keys="Chat.buyer_id", back_populates="buyer")
    chats_as_seller = relationship("Chat", foreign_keys="Chat.seller_id", back_populates="seller")
    messages = relationship("Message", back_populates="sender")


class SellerProfile(Base):
    __tablename__ = "seller_profiles"

    seller_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, unique=True)
    shop_name = Column(String(200), nullable=False)
    aadhaar_number = Column(String(50), nullable=True)
    government_license = Column(String(200), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    latitude = Column(DECIMAL(10, 8), nullable=True)
    longitude = Column(DECIMAL(11, 8), nullable=True)
    rating = Column(DECIMAL(3, 2), nullable=False, default=0.00)
    verified = Column(TINYINT(1), nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User", back_populates="seller_profile")


class BuyerProfile(Base):
    __tablename__ = "buyer_profiles"

    buyer_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, unique=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    latitude = Column(DECIMAL(10, 8), nullable=True)
    longitude = Column(DECIMAL(11, 8), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User", back_populates="buyer_profile")


class Animal(Base):
    __tablename__ = "animals"

    animal_id = Column(Integer, primary_key=True, autoincrement=True)
    seller_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    animal_type = Column(Enum(AnimalType), nullable=False)
    breed = Column(String(100), nullable=False)
    gender = Column(Enum(GenderType), nullable=False)
    age = Column(String(50), nullable=False)
    weight = Column(String(50), nullable=False)
    color = Column(String(50), nullable=True)
    price = Column(DECIMAL(12, 2), nullable=False)
    milk_yield = Column(String(50), nullable=True)
    pregnant = Column(TINYINT(1), nullable=False, default=0)
    vaccinated = Column(TINYINT(1), nullable=False, default=0)
    health_status = Column(String(100), nullable=False, default="Healthy")
    description = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    latitude = Column(DECIMAL(10, 8), nullable=True)
    longitude = Column(DECIMAL(11, 8), nullable=True)
    availability = Column(Enum(AvailabilityStatus), nullable=False, default=AvailabilityStatus.Available)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    seller = relationship("User", back_populates="animals")
    images = relationship("AnimalImage", back_populates="animal", cascade="all, delete-orphan")
    vaccinations = relationship("Vaccination", back_populates="animal", cascade="all, delete-orphan")
    disease_history = relationship("DiseaseHistory", back_populates="animal", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="animal", cascade="all, delete-orphan")


class AnimalImage(Base):
    __tablename__ = "animal_images"

    image_id = Column(Integer, primary_key=True, autoincrement=True)
    animal_id = Column(Integer, ForeignKey("animals.animal_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    image_url = Column(String(500), nullable=False)
    is_primary = Column(TINYINT(1), nullable=False, default=0)
    uploaded_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    animal = relationship("Animal", back_populates="images")


class Vaccination(Base):
    __tablename__ = "vaccinations"

    vaccination_id = Column(Integer, primary_key=True, autoincrement=True)
    animal_id = Column(Integer, ForeignKey("animals.animal_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    vaccine_name = Column(String(150), nullable=False)
    vaccination_date = Column(Date, nullable=False)
    next_due_date = Column(Date, nullable=True)
    doctor_name = Column(String(150), nullable=True)

    animal = relationship("Animal", back_populates="vaccinations")


class DiseaseHistory(Base):
    __tablename__ = "disease_history"

    history_id = Column(Integer, primary_key=True, autoincrement=True)
    animal_id = Column(Integer, ForeignKey("animals.animal_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    disease_name = Column(String(150), nullable=False)
    severity = Column(Enum(SeverityType), nullable=False, default=SeverityType.Medium)
    treatment = Column(Text, nullable=True)
    doctor = Column(String(150), nullable=True)
    diagnosis_date = Column(Date, nullable=False)

    animal = relationship("Animal", back_populates="disease_history")


class Favorite(Base):
    __tablename__ = "favorites"

    favorite_id = Column(Integer, primary_key=True, autoincrement=True)
    buyer_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    animal_id = Column(Integer, ForeignKey("animals.animal_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    buyer = relationship("User", back_populates="favorites")
    animal = relationship("Animal", back_populates="favorites")

    __table_args__ = (
        UniqueConstraint("buyer_id", "animal_id", name="uk_favorites_buyer_animal"),
    )


class Chat(Base):
    __tablename__ = "chats"

    chat_id = Column(Integer, primary_key=True, autoincrement=True)
    buyer_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    seller_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    buyer = relationship("User", foreign_keys=[buyer_id], back_populates="chats_as_buyer")
    seller = relationship("User", foreign_keys=[seller_id], back_populates="chats_as_seller")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("buyer_id", "seller_id", name="uk_chats_buyer_seller"),
    )


class Message(Base):
    __tablename__ = "messages"

    message_id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer, ForeignKey("chats.chat_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    message = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    is_read = Column(TINYINT(1), nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    chat = relationship("Chat", back_populates="messages")
    sender = relationship("User", back_populates="messages")


class Review(Base):
    __tablename__ = "reviews"

    review_id = Column(Integer, primary_key=True, autoincrement=True)
    buyer_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    seller_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    animal_id = Column(Integer, ForeignKey("animals.animal_id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    rating = Column(Integer, nullable=False)
    review = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        checkconstraint("rating BETWEEN 1 AND 5", name="chk_review_rating"),
    )


class Report(Base):
    __tablename__ = "reports"

    report_id = Column(Integer, primary_key=True, autoincrement=True)
    reported_by = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    seller_id = Column(Integer, ForeignKey("users.user_id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    animal_id = Column(Integer, ForeignKey("animals.animal_id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    report_type = Column(Enum(ReportType), nullable=False)
    reason = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(Enum(ReportStatus), nullable=False, default=ReportStatus.Pending)
    admin_action = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(TINYINT(1), nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class AIChatHistory(Base):
    __tablename__ = "ai_chat_history"

    chat_history_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    language = Column(String(20), nullable=False, default="en")
    feedback = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        checkconstraint("feedback IS NULL OR feedback BETWEEN 1 AND 5", name="chk_ai_feedback"),
    )


class DiseasePrediction(Base):
    __tablename__ = "disease_predictions"

    prediction_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    animal_id = Column(Integer, ForeignKey("animals.animal_id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    uploaded_image = Column(String(500), nullable=False)
    predicted_disease = Column(String(150), nullable=True)
    confidence_score = Column(DECIMAL(5, 4), nullable=True)
    treatment = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class PricePrediction(Base):
    __tablename__ = "price_predictions"

    prediction_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    animal_id = Column(Integer, ForeignKey("animals.animal_id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    predicted_price = Column(DECIMAL(12, 2), nullable=False)
    actual_price = Column(DECIMAL(12, 2), nullable=True)
    model_version = Column(String(50), nullable=False)
    prediction_time = Column(DateTime, nullable=False, default=datetime.utcnow)


class LoginHistory(Base):
    __tablename__ = "login_history"

    login_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    login_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    logout_time = Column(DateTime, nullable=True)
    ip_address = Column(String(45), nullable=True)
    device = Column(String(255), nullable=True)
