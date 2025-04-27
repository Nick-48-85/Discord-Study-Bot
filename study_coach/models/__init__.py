"""
Models package for the Discord Adaptive Study Coach.
"""

from .models import (
    DifficultyLevel,
    StudyMaterial,
    QuizQuestion,
    QuizAttempt,
    UserProfile,
    StudySession
)

from .enhanced_models import (
    FeedbackRating,
    QuestionFeedback,
    EnhancedQuizQuestion,
    QAChangelog
)

# Re-export for convenient imports
__all__ = [
    'DifficultyLevel',
    'StudyMaterial', 
    'QuizQuestion', 
    'QuizAttempt', 
    'UserProfile', 
    'StudySession',
    'FeedbackRating',
    'QuestionFeedback',
    'EnhancedQuizQuestion',
    'QAChangelog'
]
