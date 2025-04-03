from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    login = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String, default="student")
    points = Column(Integer, default=0)
    modules = relationship("Module", back_populates="user")
    character = relationship("Character", back_populates="user", uselist=False)
    progress = relationship("Progress", back_populates="user")


class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    type = Column(String)
    content = Column(JSON)
    image = Column(String, nullable=True)
    points = Column(Integer, default=0)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="modules")
    progress = relationship("Progress", back_populates="module")


class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    hair = Column(String, default="hair_1")
    face = Column(String, default="face_1")
    costume = Column(String, default="costume_1")
    shoes = Column(String, default="shoes_1")
    skills = Column(JSON, default={"strength": 1, "intelligence": 1, "agility": 1})
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

    user = relationship("User", back_populates="character")


class Progress(Base):
    __tablename__ = "progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    module_id = Column(Integer, ForeignKey("modules.id"))
    completed = Column(Boolean, default=False)

    user = relationship("User", back_populates="progress")
    module = relationship("Module", back_populates="progress")
