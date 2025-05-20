from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base
from datetime import datetime, timezone
import uuid

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    nickname = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

class RefreshToken(Base):
    __tablename__ = 'refresh_tokens'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    fingerprint = Column(String, nullable=False)  
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=False) 
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="refresh_tokens")

class GameSession(Base):
    __tablename__ = 'game_sessions'
    
    id = Column(String(8), primary_key=True)  
    creator_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    status = Column(Enum('waiting', 'active', 'finished', name='session_status'), 
                    default='waiting')
    created_at = Column(DateTime, default=datetime.utcnow)
    max_players = Column(Integer, default=2)
    
    players = relationship("SessionPlayer", back_populates="session")

    current_turn_user_id = Column(Integer, ForeignKey("users.id"))
    is_current_turn_active = Column(Boolean, default=False)
    turn_number = Column(Integer, default=0)
    players_order = Column(JSON, default=[])  

class SessionPlayer(Base):
    __tablename__ = 'session_players'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(8), ForeignKey('game_sessions.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    is_ready = Column(Boolean, default=False)
    is_gm = Column(Boolean, default=False)
    character_id = Column(Integer, ForeignKey("characters.id"))

    session = relationship("GameSession", back_populates="players")
    user = relationship("User")

class Character(Base):
    __tablename__ = "characters"
    
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    race = Column(String)  
    class_ = Column("class", String)  # переименовываем для SQL
    strength = Column(Integer, default=1)
    dexterity = Column(Integer, default=1)
    intelligence = Column(Integer, default=1)
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)

class NPC(Base):
    __tablename__ = "npcs"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("game_sessions.id"))
    name = Column(String, index=True)
    image_url = Column(String)
    description = Column(String, nullable=True)

class GameMap(Base):
    __tablename__ = "game_maps"
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String, ForeignKey("game_sessions.id"))
    name = Column(String)
    background_image = Column(String)  
    grid_size = Column(Integer, default=50)  
    width = Column(Integer)  
    height = Column(Integer)  
    walls = Column(JSON, default=[])  
    obstacles = Column(JSON, default=[]) 