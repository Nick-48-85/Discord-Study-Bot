"""
Services package for the Discord Adaptive Study Coach.
"""

from .database import DatabaseService
from .ollama import OllamaService, PromptType
from .qa_dataset import QADatasetService
from .summarization import EnhancedSummarizationService
from .prompts import SummarizationPrompts, QuizPrompts, FlashcardPrompts, DetectionPrompts

# OllamaEnhancedService is now just an alias for OllamaService for backward compatibility
from .ollama import OllamaService as OllamaEnhancedService
