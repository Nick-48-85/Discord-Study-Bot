"""
Usage example for the enhanced study dataset and LLM request handler.
"""

import asyncio
from typing import List, Dict, Any
import uuid

from study_coach.services.database import DatabaseService
from study_coach.services.ollama import OllamaService, PromptType
from study_coach.services.qa_dataset import QADatasetService
from study_coach.models.models import StudyMaterial
from study_coach.models.enhanced_models import EnhancedQuizQuestion, QuestionFeedback


async def demo_enhanced_features():
    """
    Demonstrate the enhanced study dataset and LLM request handler features.
    """
    print("Initializing services...")
    
    # Initialize services
    db_service = DatabaseService()
    ollama_service = OllamaService("http://localhost:11434")
    qa_service = QADatasetService(db_service, ollama_service)
    
    # Create a sample study material
    user_id = str(uuid.uuid4())
    material_id = str(uuid.uuid4())
    
    study_material = StudyMaterial(
        id=material_id,
        title="Sample Study Material",
        user_id=user_id,
        content_type="text",
        content_hash="sample_hash",
        content_path="sample_path.txt",
        topics=["Machine Learning", "Python"]
    )
    
    # Save the study material
    print("Creating sample study material...")
    await db_service.create_material(study_material)
    
    # Step 1: Generate QA pairs
    print("\nGenerating QA pairs...")
    questions = await qa_service.generate_qa_pairs(
        material_id=material_id,
        num_questions=3,
        question_types=["multiple_choice", "short_answer"],
        difficulty="medium",
        topics=["Machine Learning"]
    )
    
    print(f"Generated {len(questions)} QA pairs")
    for i, q in enumerate(questions):
        print(f"Question {i+1}: {q.question}")
    
    # Step 2: Generate adversarial examples
    print("\nGenerating adversarial examples...")
    adversarial_questions = await qa_service.generate_adversarial_examples(
        material_id=material_id,
        num_examples=2
    )
    
    print(f"Generated {len(adversarial_questions)} adversarial examples")
    for i, q in enumerate(adversarial_questions):
        print(f"Adversarial Question {i+1}: {q.question}")
    
    # Step 3: Record feedback on questions
    print("\nRecording feedback on questions...")
    if questions:
        feedback_id = await qa_service.record_question_feedback(
            question_id=questions[0].id,
            user_id=user_id,
            is_correct=True,
            is_helpful=True,
            difficulty_rating=3,
            feedback_text="This was a helpful question!"
        )
        print(f"Recorded feedback with ID: {feedback_id}")
    
    # Step 4: Evaluate and update questions
    print("\nEvaluating and updating questions...")
    update_stats = await qa_service.evaluate_and_update_questions(
        material_id=material_id,
        threshold=0.3
    )
    print(f"Update stats: {update_stats}")
    
    # Step 5: Demonstrate temperature settings with different prompt types
    print("\nDemonstrating temperature settings with different prompt types...")
    
    # Factual task - uses temperature 0.3
    print("\nFactual task (summarization) - temperature=0.3:")
    summary = await ollama_service.summarize_text(
        text="Machine learning is a branch of artificial intelligence that focuses on building systems that learn from data. "
             "It includes supervised learning, unsupervised learning, and reinforcement learning approaches. "
             "Supervised learning uses labeled training data, while unsupervised learning finds patterns in unlabeled data.",
        max_points=3
    )
    print("Summary bullets:")
    for bullet in summary:
        print(f"- {bullet}")
    
    # Creative task - uses temperature 0.7
    print("\nCreative task (flashcard generation) - temperature=0.7:")
    flashcards = await ollama_service.generate_flashcards(
        text="Machine learning is a branch of artificial intelligence that focuses on building systems that learn from data. "
             "It includes supervised learning, unsupervised learning, and reinforcement learning approaches. "
             "Supervised learning uses labeled training data, while unsupervised learning finds patterns in unlabeled data.",
        num_cards=2
    )
    print("Flashcards:")
    for i, card in enumerate(flashcards):
        print(f"Card {i+1} - Front: {card.get('front')}")
        print(f"Card {i+1} - Back: {card.get('back')}")
    
    # Structured JSON response
    print("\nStructured JSON response using generate_structured_completion:")
    schema = {
        "type": "object",
        "properties": {
            "topic": {"type": "string"},
            "difficulty": {"type": "string", "enum": ["easy", "medium", "hard"]},
            "concepts": {
                "type": "array",
                "items": {"type": "string"}
            }
        }
    }
    
    structured_response = await ollama_service.generate_structured_completion(
        prompt="Analyze machine learning as a topic and list key concepts. Provide difficulty level.",
        prompt_type=PromptType.FACTUAL,
        schema=schema,
        max_tokens=500
    )
    
    print(f"Structured response: {structured_response}")
    

if __name__ == "__main__":
    asyncio.run(demo_enhanced_features())
