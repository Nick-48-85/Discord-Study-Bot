"""
Database models for the Discord Adaptive Study Coach.
"""

import datetime
from typing import List, Dict, Optional, Any, Union
from enum import Enum


class DifficultyLevel(str, Enum):
    """Difficulty levels for quizzes and content."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class StudyMaterial:
    """Model for storing study material information."""
    def __init__(
        self,
        id: str,
        title: str,
        user_id: str,
        content_type: str,  # "pdf", "text", "url"
        content_hash: str,
        content_path: Optional[str] = None,
        url: Optional[str] = None,
        topics: List[str] = None,
        embedding_id: Optional[str] = None,
        created_at: datetime.datetime = None,
        updated_at: datetime.datetime = None
    ):
        self.id = id
        self.title = title
        self.user_id = user_id
        self.content_type = content_type
        self.content_hash = content_hash
        self.content_path = content_path
        self.url = url
        self.topics = topics or []
        self.embedding_id = embedding_id
        self.created_at = created_at or datetime.datetime.now()
        self.updated_at = updated_at or datetime.datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for database storage."""
        return {
            "id": self.id,
            "title": self.title,
            "user_id": self.user_id,
            "content_type": self.content_type,
            "content_hash": self.content_hash,
            "content_path": self.content_path,
            "url": self.url,
            "topics": self.topics,
            "embedding_id": self.embedding_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StudyMaterial':
        """Create model from dictionary."""
        # Create a copy of the data to avoid modifying the original
        data_copy = data.copy()
        
        # Handle MongoDB _id field conversion to id
        if "_id" in data_copy:
            if "id" not in data_copy:
                data_copy["id"] = str(data_copy["_id"])
            data_copy.pop("_id")
            
        return cls(**data_copy)


class QuizQuestion:
    """Model for storing quiz questions."""
    def __init__(
        self,
        id: str,
        material_id: str,
        question: str,
        question_type: str,  # "multiple_choice", "short_answer", "flashcard"
        options: List[str] = None,
        correct_answer: Union[str, int] = None,
        topic: Optional[str] = None,
        difficulty: DifficultyLevel = DifficultyLevel.MEDIUM,
        created_at: datetime.datetime = None
    ):
        self.id = id
        self.material_id = material_id
        self.question = question
        self.question_type = question_type
        self.options = options or []
        self.correct_answer = correct_answer
        self.topic = topic
        self.difficulty = difficulty
        self.created_at = created_at or datetime.datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for database storage."""
        return {
            "id": self.id,
            "material_id": self.material_id,
            "question": self.question,
            "question_type": self.question_type,
            "options": self.options,
            "correct_answer": self.correct_answer,
            "topic": self.topic,
            "difficulty": self.difficulty.value,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuizQuestion':
        """Create model from dictionary."""
        # Create a copy of the data to avoid modifying the original
        data_copy = data.copy()
        
        # Handle MongoDB _id field conversion to id
        if "_id" in data_copy:
            if "id" not in data_copy:
                data_copy["id"] = str(data_copy["_id"])
            data_copy.pop("_id")
            
        if isinstance(data_copy.get("difficulty"), str):
            data_copy["difficulty"] = DifficultyLevel(data_copy["difficulty"])
        return cls(**data_copy)


class QuizAttempt:
    """Model for storing quiz attempts by users."""
    def __init__(
        self,
        id: str,
        user_id: str,
        question_id: str,
        answer: Union[str, int],
        is_correct: bool,
        time_taken_seconds: float,
        session_id: str,
        created_at: datetime.datetime = None
    ):
        self.id = id
        self.user_id = user_id
        self.question_id = question_id
        self.answer = answer
        self.is_correct = is_correct
        self.time_taken_seconds = time_taken_seconds
        self.session_id = session_id
        self.created_at = created_at or datetime.datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for database storage."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "question_id": self.question_id,
            "answer": self.answer,
            "is_correct": self.is_correct,
            "time_taken_seconds": self.time_taken_seconds,
            "session_id": self.session_id,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuizAttempt':
        """Create model from dictionary."""
        # Create a copy of the data to avoid modifying the original
        data_copy = data.copy()
        
        # Handle MongoDB _id field conversion to id
        if "_id" in data_copy:
            if "id" not in data_copy:
                data_copy["id"] = str(data_copy["_id"])
            data_copy.pop("_id")
            
        return cls(**data_copy)


class UserProfile:
    """Model for storing user profiles."""
    def __init__(
        self,
        id: str,
        discord_id: str,
        username: str,
        difficulty_preference: DifficultyLevel = DifficultyLevel.MEDIUM,
        topics_of_interest: List[str] = None,
        session_count: int = 0,
        total_questions_answered: int = 0,
        correct_answers: int = 0,
        created_at: datetime.datetime = None,
        last_active: datetime.datetime = None
    ):
        self.id = id
        self.discord_id = discord_id
        self.username = username
        self.difficulty_preference = difficulty_preference
        self.topics_of_interest = topics_of_interest or []
        self.session_count = session_count
        self.total_questions_answered = total_questions_answered
        self.correct_answers = correct_answers
        self.created_at = created_at or datetime.datetime.now()
        self.last_active = last_active or datetime.datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for database storage."""
        return {
            "id": self.id,
            "discord_id": self.discord_id,
            "username": self.username,
            "difficulty_preference": self.difficulty_preference.value,
            "topics_of_interest": self.topics_of_interest,
            "session_count": self.session_count,
            "total_questions_answered": self.total_questions_answered,
            "correct_answers": self.correct_answers,
            "created_at": self.created_at,
            "last_active": self.last_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProfile':
        """Create model from dictionary."""
        # Create a copy of the data to avoid modifying the original
        data_copy = data.copy()
        
        # Handle MongoDB _id field conversion to id - more robust handling
        if "_id" in data_copy:
            # Always use _id as id (even if id exists) to ensure consistency
            data_copy["id"] = str(data_copy.pop("_id"))
        if isinstance(data_copy.get("difficulty_preference"), str):
            data_copy["difficulty_preference"] = DifficultyLevel(data_copy["difficulty_preference"])
        
        return cls(**data_copy)


class StudySession:
    """Model for storing study sessions."""
    def __init__(
        self,
        id: str,
        user_id: str,
        material_id: str,
        session_type: str,  # "quiz", "flashcard", "summary"
        start_time: datetime.datetime,
        end_time: Optional[datetime.datetime] = None,
        score: Optional[float] = None,
        total_questions: int = 0,
        correct_answers: int = 0,
        difficulty: Optional[DifficultyLevel] = None,
        topics: List[str] = None
    ):
        self.id = id
        self.user_id = user_id
        self.material_id = material_id
        self.session_type = session_type
        self.start_time = start_time
        self.end_time = end_time
        self.score = score
        self.total_questions = total_questions
        self.correct_answers = correct_answers
        self.difficulty = difficulty
        self.topics = topics or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for database storage."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "material_id": self.material_id,
            "session_type": self.session_type,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "score": self.score,
            "total_questions": self.total_questions,
            "correct_answers": self.correct_answers,
            "difficulty": self.difficulty.value if self.difficulty else None,
            "topics": self.topics
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StudySession':
        """Create model from dictionary."""
        # Create a copy of the data to avoid modifying the original
        data_copy = data.copy()
        
        # Handle MongoDB _id field conversion to id
        if "_id" in data_copy:
            if "id" not in data_copy:
                data_copy["id"] = str(data_copy["_id"])
            data_copy.pop("_id")
            
        if data_copy.get("difficulty") and isinstance(data_copy["difficulty"], str):
            data_copy["difficulty"] = DifficultyLevel(data_copy["difficulty"])
        return cls(**data_copy)
