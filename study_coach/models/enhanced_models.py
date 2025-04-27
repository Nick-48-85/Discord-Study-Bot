"""
Enhanced database models for the Discord Adaptive Study Coach.
"""

import datetime
from typing import List, Dict, Optional, Any, Union
from enum import Enum


class DifficultyLevel(str, Enum):
    """Difficulty levels for quizzes and content."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class FeedbackRating(str, Enum):
    """Feedback ratings for content quality."""
    EXCELLENT = "excellent"
    GOOD = "good"
    NEUTRAL = "neutral"
    POOR = "poor"
    VERY_POOR = "very_poor"


class QuestionFeedback:
    """Model for storing user feedback on quiz questions."""
    def __init__(
        self,
        id: str,
        question_id: str,
        user_id: str,
        is_correct: bool,
        is_helpful: Optional[bool] = None,
        difficulty_rating: Optional[int] = None,  # 1-5 scale
        feedback_text: Optional[str] = None,
        created_at: datetime.datetime = None
    ):
        self.id = id
        self.question_id = question_id
        self.user_id = user_id
        self.is_correct = is_correct
        self.is_helpful = is_helpful
        self.difficulty_rating = difficulty_rating
        self.feedback_text = feedback_text
        self.created_at = created_at or datetime.datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for database storage."""
        return {
            "id": self.id,
            "question_id": self.question_id,
            "user_id": self.user_id,
            "is_correct": self.is_correct,
            "is_helpful": self.is_helpful,
            "difficulty_rating": self.difficulty_rating,
            "feedback_text": self.feedback_text,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuestionFeedback':
        """Create model from dictionary."""
        # Create a copy of the data to avoid modifying the original
        data_copy = data.copy()
        
        # Handle MongoDB _id field conversion to id
        if "_id" in data_copy:
            if "id" not in data_copy:
                data_copy["id"] = str(data_copy["_id"])
            data_copy.pop("_id")
            
        return cls(**data_copy)


class EnhancedQuizQuestion:
    """Enhanced model for storing quiz questions with quality metrics."""
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
        created_at: datetime.datetime = None,
        updated_at: Optional[datetime.datetime] = None,
        is_adversarial: bool = False,
        adversarial_type: Optional[str] = None,
        quality_metrics: Optional[Dict[str, Any]] = None,
        improvement_notes: Optional[str] = None,
        version: int = 1
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
        self.updated_at = updated_at
        self.is_adversarial = is_adversarial
        self.adversarial_type = adversarial_type
        self.quality_metrics = quality_metrics or {
            "accuracy": 0.0,
            "helpfulness": 0.0,
            "total_attempts": 0,
            "updated_at": None
        }
        self.improvement_notes = improvement_notes
        self.version = version
    
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
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_adversarial": self.is_adversarial,
            "adversarial_type": self.adversarial_type,
            "quality_metrics": self.quality_metrics,
            "improvement_notes": self.improvement_notes,
            "version": self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnhancedQuizQuestion':
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


class QAChangelog:
    """Model for storing change history of quiz questions."""
    def __init__(
        self,
        id: str,
        question_id: str,
        material_id: str,
        action: str,  # "created", "updated", "removed"
        details: str,
        timestamp: datetime.datetime,
        qa_data: Dict[str, Any],
        previous_data: Optional[Dict[str, Any]] = None
    ):
        self.id = id
        self.question_id = question_id
        self.material_id = material_id
        self.action = action
        self.details = details
        self.timestamp = timestamp
        self.qa_data = qa_data
        self.previous_data = previous_data
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for database storage."""
        result = {
            "id": self.id,
            "question_id": self.question_id,
            "material_id": self.material_id,
            "action": self.action,
            "details": self.details,
            "timestamp": self.timestamp,
            "qa_data": self.qa_data
        }
        
        if self.previous_data:
            result["previous_data"] = self.previous_data
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QAChangelog':
        """Create model from dictionary."""
        # Create a copy of the data to avoid modifying the original
        data_copy = data.copy()
        
        # Handle MongoDB _id field conversion to id
        if "_id" in data_copy:
            if "id" not in data_copy:
                data_copy["id"] = str(data_copy["_id"])
            data_copy.pop("_id")
            
        return cls(**data_copy)
