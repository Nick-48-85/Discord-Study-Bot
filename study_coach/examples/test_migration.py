"""
Test script to verify the OllamaService functionality.

This script performs a simple completion test using the services package imports.
"""

import asyncio
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from study_coach.services import OllamaService
from study_coach.services.ollama import OllamaService, PromptType


async def test_services():
    """Test that services are properly migrated."""
    
    # Create a basic OllamaService (which should now be the enhanced service)
    service = OllamaService(base_url="http://localhost:11434")
    
    # Verify it's actually the enhanced service
    print(f"Service type: {type(service).__name__}")
    print(f"Has temperature_settings: {hasattr(service, 'temperature_settings')}")
    
    # Test a simple completion using factual/creative settings
    try:
        # Try with factual prompt type
        factual_response = await service.generate_structured_completion(
            prompt="Define what an LLM is",
            prompt_type=PromptType.FACTUAL,
            max_tokens=100,
            schema={"definition": "string", "examples": ["string"]}
        )
        
        print("\nFactual response:")
        print(f"Temperature: {service.temperature_settings[PromptType.FACTUAL]}")
        print(f"Response: {factual_response}")
        
        # Try with creative prompt type
        creative_response = await service.generate_completion(
            prompt="Write a short poem about AI",
            temperature=service.temperature_settings[PromptType.CREATIVE],
            max_tokens=100
        )
        
        print("\nCreative response:")
        print(f"Temperature: {service.temperature_settings[PromptType.CREATIVE]}")
        print(f"Response: {creative_response[:100]}...")
        
    except Exception as e:
        print(f"Error during test: {type(e).__name__}: {str(e)}")
    
    print("\nTest complete!")


if __name__ == "__main__":
    asyncio.run(test_services())
