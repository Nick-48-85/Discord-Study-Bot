"""
Database service for the Discord Adaptive Study Coach.
"""

import os
import uuid
import motor.motor_asyncio
from typing import List, Dict, Any, Optional, Union
from ..models.models import (
    UserProfile, StudyMaterial, QuizQuestion, QuizAttempt, StudySession
)


class DatabaseService:
    """Service for interacting with the MongoDB database."""
    
    def __init__(self, mongo_uri=None):
        """Initialize database connection."""
        self.mongo_uri = mongo_uri or os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.client = motor.motor_asyncio.AsyncIOMotorClient(self.mongo_uri)
        self.db = self.client.study_coach
        
        # Collections
        self.users = self.db.users
        self.materials = self.db.materials
        self.questions = self.db.questions
        self.attempts = self.db.attempts
        self.sessions = self.db.sessions
    
    async def create_indexes(self):
        """Create necessary indexes for the database."""
        await self.users.create_index("discord_id", unique=True)
        await self.materials.create_index("user_id")
        await self.materials.create_index("content_hash")
        await self.questions.create_index("material_id")
        await self.attempts.create_index("user_id")
        await self.attempts.create_index("session_id")
        await self.sessions.create_index("user_id")
      # User profile methods
    async def get_user_by_discord_id(self, discord_id: str) -> Optional[UserProfile]:
        """Get a user profile by Discord ID."""
        user_data = await self.users.find_one({"discord_id": discord_id})
        print(f"Database find_one result for discord_id {discord_id}: {user_data}")
        if user_data:
            # Make a copy and explicitly convert _id to string for safety
            if "_id" in user_data:
                user_data["id"] = str(user_data["_id"])
                user_data.pop("_id")
            return UserProfile.from_dict(user_data)
        return None
    
    async def create_user(self, user: UserProfile) -> str:
        """Create a new user profile."""
        if not user.id:
            user.id = str(uuid.uuid4())
        await self.users.insert_one(user.to_dict())
        return user.id
    
    async def update_user(self, user: UserProfile) -> bool:
        """Update a user profile."""
        result = await self.users.replace_one({"id": user.id}, user.to_dict())
        return result.modified_count > 0
    
    # Study material methods
    async def create_material(self, material: StudyMaterial) -> str:
        """Create a new study material."""
        if not material.id:
            material.id = str(uuid.uuid4())
        await self.materials.insert_one(material.to_dict())
        return material.id
    
    async def get_material_by_id(self, material_id: str) -> Optional[StudyMaterial]:
        """Get a study material by ID."""
        material_data = await self.materials.find_one({"id": material_id})
        return StudyMaterial.from_dict(material_data) if material_data else None
    
    async def get_materials_by_user(self, user_id: str) -> List[StudyMaterial]:
        """Get all study materials for a user."""
        cursor = self.materials.find({"user_id": user_id})
        materials = []
        async for doc in cursor:
            materials.append(StudyMaterial.from_dict(doc))
        return materials
    
    # Question methods
    async def create_question(self, question: QuizQuestion) -> str:
        """Create a new quiz question."""
        if not question.id:
            question.id = str(uuid.uuid4())
        await self.questions.insert_one(question.to_dict())
        return question.id
    
    async def create_questions_batch(self, questions: List[QuizQuestion]) -> List[str]:
        """Create multiple quiz questions at once."""
        for question in questions:
            if not question.id:
                question.id = str(uuid.uuid4())
        
        await self.questions.insert_many([q.to_dict() for q in questions])
        return [q.id for q in questions]
    
    async def get_questions_by_material(self, material_id: str) -> List[QuizQuestion]:
        """Get all questions for a specific study material."""
        cursor = self.questions.find({"material_id": material_id})
        questions = []
        async for doc in cursor:
            questions.append(QuizQuestion.from_dict(doc))
        return questions
    
    # Quiz attempt methods
    async def create_attempt(self, attempt: QuizAttempt) -> str:
        """Record a quiz attempt by a user."""
        if not attempt.id:
            attempt.id = str(uuid.uuid4())
        await self.attempts.insert_one(attempt.to_dict())
        return attempt.id
    
    async def get_attempts_by_session(self, session_id: str) -> List[QuizAttempt]:
        """Get all attempts for a specific session."""
        cursor = self.attempts.find({"session_id": session_id})
        attempts = []
        async for doc in cursor:
            attempts.append(QuizAttempt.from_dict(doc))
        return attempts
    
    # Study session methods
    async def create_session(self, session: StudySession) -> str:
        """Create a new study session."""
        if not session.id:
            session.id = str(uuid.uuid4())
        await self.sessions.insert_one(session.to_dict())
        return session.id
    
    async def update_session(self, session: StudySession) -> bool:
        """Update a study session."""
        result = await self.sessions.replace_one({"id": session.id}, session.to_dict())
        return result.modified_count > 0
    
    async def get_session_by_id(self, session_id: str) -> Optional[StudySession]:
        """Get a study session by ID."""
        session_data = await self.sessions.find_one({"id": session_id})
        return StudySession.from_dict(session_data) if session_data else None
    
    async def get_sessions_by_user(self, user_id: str, limit: int = 10) -> List[StudySession]:
        """Get recent study sessions for a user."""
        cursor = self.sessions.find({"user_id": user_id}).sort("start_time", -1).limit(limit)
        sessions = []
        async for doc in cursor:
            sessions.append(StudySession.from_dict(doc))
        return sessions
    
    async def get_sessions_by_date(self, user_id: str, date) -> List[StudySession]:
        """Get all sessions for a user on a specific date."""
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        cursor = self.sessions.find({
            "user_id": user_id,
            "start_time": {"$gte": start_of_day, "$lte": end_of_day}
        })
        
        sessions = []
        async for doc in cursor:
            sessions.append(StudySession.from_dict(doc))
        return sessions
