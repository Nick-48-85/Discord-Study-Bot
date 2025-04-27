"""
Integration example showing how to use the enhanced QA dataset and LLM request handler
with the study coach bot.
"""

import os
import asyncio
from typing import Dict, Any, List

from study_coach.services import DatabaseService, OllamaEnhancedService, QADatasetService, PromptType
from study_coach.models import StudyMaterial, EnhancedQuizQuestion


class EnhancedStudyCoachIntegration:
    """
    Integration class for enhanced study coach features.
    
    This class demonstrates how to integrate the enhanced QA dataset and
    LLM request handler with the existing study coach bot.
    """
    
    def __init__(self):
        """Initialize integration components."""
        # Initialize services
        self.db_service = DatabaseService()
        self.ollama = OllamaEnhancedService(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        )
        self.qa_service = QADatasetService(self.db_service, self.ollama)
    
    async def initialize(self):
        """Initialize database connections and create indexes."""
        await self.db_service.create_indexes()
    
    async def enhance_study_material(self, material_id: str) -> Dict[str, Any]:
        """
        Enhance a study material by generating QA pairs and adversarial examples.
        
        Args:
            material_id: ID of the study material to enhance
            
        Returns:
            Dict containing enhancement results
        """
        # Get the study material
        material = await self.db_service.get_material_by_id(material_id)
        if not material:
            raise ValueError(f"Study material with ID {material_id} not found")
        
        results = {
            "material_id": material_id,
            "material_title": material.title,
            "qa_pairs_generated": 0,
            "adversarial_examples_generated": 0
        }
        
        # Generate QA pairs
        try:
            print(f"Generating QA pairs for material: {material.title}")
            qa_pairs = await self.qa_service.generate_qa_pairs(
                material_id=material_id,
                num_questions=10,  # Generate 10 questions
                question_types=["multiple_choice", "short_answer"],
                difficulty=material.difficulty_level.value if hasattr(material, "difficulty_level") else "medium",
                topics=material.topics
            )
            results["qa_pairs_generated"] = len(qa_pairs)
            
            # Generate adversarial examples
            print(f"Generating adversarial examples for material: {material.title}")
            adversarial_examples = await self.qa_service.generate_adversarial_examples(
                material_id=material_id,
                num_examples=3,  # Generate 3 adversarial examples
                base_on_existing=True
            )
            results["adversarial_examples_generated"] = len(adversarial_examples)
            
            print(f"Enhancement complete for material: {material.title}")
        except Exception as e:
            print(f"Error enhancing material {material_id}: {str(e)}")
            results["error"] = str(e)
        
        return results
    
    async def process_user_feedback(self, question_id: str, user_id: str, 
                                    is_correct: bool, is_helpful: bool = None, 
                                    difficulty_rating: int = None,
                                    feedback_text: str = None) -> Dict[str, Any]:
        """
        Process user feedback on a question.
        
        Args:
            question_id: ID of the question
            user_id: ID of the user providing feedback
            is_correct: Whether the user answered correctly
            is_helpful: Whether the user found the question helpful
            difficulty_rating: User rating of difficulty (1-5)
            feedback_text: Optional text feedback
            
        Returns:
            Dict containing feedback processing results
        """
        try:
            # Record the feedback
            feedback_id = await self.qa_service.record_question_feedback(
                question_id=question_id,
                user_id=user_id,
                is_correct=is_correct,
                is_helpful=is_helpful,
                difficulty_rating=difficulty_rating,
                feedback_text=feedback_text
            )
            
            return {
                "success": True,
                "feedback_id": feedback_id,
                "question_id": question_id,
                "user_id": user_id
            }
        except Exception as e:
            print(f"Error processing feedback for question {question_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_llm_completion(self, prompt: str, is_factual: bool = True) -> str:
        """
        Get LLM completion with automatic temperature selection.
        
        Args:
            prompt: The prompt to send to the model
            is_factual: Whether this is a factual task (True) or creative task (False)
            
        Returns:
            LLM completion text
        """
        prompt_type = PromptType.FACTUAL if is_factual else PromptType.CREATIVE
        
        response = await self.ollama.generate_completion(
            prompt=prompt,
            model="llama2:7b",  # Default model, can be configured
            temperature=self.ollama.temperature_settings[prompt_type],
            top_p=self.ollama.top_p,
            max_tokens=500
        )
        
        return response
    
    async def get_structured_completion(self, prompt: str, schema: Dict[str, Any],
                                       is_factual: bool = True) -> Dict[str, Any]:
        """
        Get structured LLM completion with automatic temperature selection.
        
        Args:
            prompt: The prompt to send to the model
            schema: JSON schema for the response
            is_factual: Whether this is a factual task (True) or creative task (False)
            
        Returns:
            Structured LLM response as a dictionary
        """
        prompt_type = PromptType.FACTUAL if is_factual else PromptType.CREATIVE
        
        response = await self.ollama.generate_structured_completion(
            prompt=prompt,
            prompt_type=prompt_type,
            model="llama2:7b",  # Default model, can be configured
            schema=schema,
            max_tokens=1000
        )
        
        return response
    
    async def cleanup(self):
        """Clean up resources."""
        # Close any open connections
        pass


async def main():
    """Main function to demonstrate the integration."""
    # Create the integration
    integration = EnhancedStudyCoachIntegration()
    
    # Initialize
    await integration.initialize()
    
    # Example: Get factual information with temperature=0.3
    factual_response = await integration.get_llm_completion(
        prompt="Explain the concept of neural networks in 3 sentences.",
        is_factual=True
    )
    print(f"\nFactual Response (temperature=0.3):\n{factual_response}")
    
    # Example: Get creative content with temperature=0.7
    creative_response = await integration.get_llm_completion(
        prompt="Generate an analogy that compares machine learning to cooking.",
        is_factual=False
    )
    print(f"\nCreative Response (temperature=0.7):\n{creative_response}")
    
    # Example: Get structured response
    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "points": {"type": "array", "items": {"type": "string"}},
            "difficulty": {"type": "string", "enum": ["beginner", "intermediate", "advanced"]}
        }
    }
    
    structured_response = await integration.get_structured_completion(
        prompt="Explain reinforcement learning. Format as a mini-lesson with title, 3 key points, and difficulty level.",
        schema=schema,
        is_factual=True
    )
    print(f"\nStructured Response:\n{structured_response}")
    
    # Cleanup
    await integration.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
