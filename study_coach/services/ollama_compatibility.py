"""
This module exists for backward compatibility only.
It imports and re-exports OllamaEnhancedService as OllamaService.
All new code should directly import from ollama_enhanced.py.
"""

# Re-export OllamaEnhancedService as OllamaService for backward compatibility
from .ollama_enhanced import OllamaEnhancedService as OllamaService
from .ollama_enhanced import PromptType

# This effectively makes "from .ollama import OllamaService" work,
# but provides the enhanced implementation.
