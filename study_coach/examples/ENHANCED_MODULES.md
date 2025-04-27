# Enhanced Study Dataset and LLM Handler Documentation

This document provides detailed information about the enhanced study dataset and LLM request handler modules for the OwlMind Study Coach system.

## Table of Contents

1. [Overview](#overview)
2. [Enhanced Study Dataset](#enhanced-study-dataset)
    - [Automatic QA Generation](#automatic-qa-generation)
    - [User Feedback System](#user-feedback-system)
    - [Quality Control System](#quality-control-system)
    - [Adversarial Examples](#adversarial-examples)
    - [MongoDB Change Logging](#mongodb-change-logging)
3. [Enhanced LLM Request Handler](#enhanced-llm-request-handler)
    - [Temperature Control](#temperature-control)
    - [JSON Response Format](#json-response-format)
    - [Prompt Type Classification](#prompt-type-classification)
4. [Integration Guide](#integration-guide)
5. [API Reference](#api-reference)

## Overview

The enhanced modules provide:

1. An improved study dataset management system that automatically generates, tracks, and improves question-answer pairs based on user feedback.
2. An intelligent LLM request handler that sets appropriate parameters based on the task type and returns consistently structured responses.

## Enhanced Study Dataset

The enhanced study dataset module (`QADatasetService`) provides comprehensive management of question-answer pairs.

### Automatic QA Generation

The system can automatically generate QA pairs from study materials:

```python
questions = await qa_service.generate_qa_pairs(
    material_id=material_id,
    num_questions=10,
    question_types=["multiple_choice", "short_answer"],
    difficulty="medium",
    topics=["Machine Learning"]
)
```

- `num_questions`: Controls how many questions to generate
- `question_types`: Types of questions (multiple_choice, short_answer)
- `difficulty`: Level of question difficulty (easy, medium, hard)
- `topics`: Specific topics to focus on

### User Feedback System

The system captures detailed user feedback on each question:

```python
feedback_id = await qa_service.record_question_feedback(
    question_id=question_id,
    user_id=user_id,
    is_correct=True,
    is_helpful=True,
    difficulty_rating=3,  # 1-5 scale
    feedback_text="This was a helpful question!"
)
```

Feedback metrics include:
- Correctness (was the user's answer correct?)
- Helpfulness (did the user find the question helpful?)
- Difficulty rating (user-perceived difficulty)
- Free-text feedback

### Quality Control System

The system periodically evaluates questions and improves or removes low-quality ones:

```python
update_stats = await qa_service.evaluate_and_update_questions(
    material_id=material_id,
    threshold=0.3  # Quality threshold (0.0-1.0)
)
```

The quality control process:
1. Computes quality metrics for each question based on user feedback
2. Identifies low-quality questions (below threshold)
3. For very poor questions: removes them from the dataset
4. For moderately poor questions: attempts to improve them using the LLM
5. Tracks all changes in the changelog

### Adversarial Examples

The system can generate challenging "adversarial" examples to test understanding:

```python
adversarial_questions = await qa_service.generate_adversarial_examples(
    material_id=material_id,
    num_examples=3,
    base_on_existing=True  # Use existing questions as inspiration
)
```

Adversarial examples focus on:
- Edge cases and common misconceptions
- Subtle distinctions requiring careful reading
- Situations where surface understanding is insufficient
- Problems with similar-looking but incorrect answers

### MongoDB Change Logging

All changes to the QA dataset are logged in MongoDB with detailed change records:

```json
{
    "id": "log-uuid-here",
    "question_id": "question-uuid-here",
    "material_id": "material-uuid-here",
    "action": "updated",
    "details": "Improved question clarity based on user feedback",
    "timestamp": "2025-04-27T14:30:00.000Z",
    "qa_data": { /* Current question data */ },
    "previous_data": { /* Previous question data */ }
}
```

This provides:
- Complete audit trail of all changes
- Ability to roll back problematic changes
- Insights into dataset evolution over time
- Data for meta-analysis of improvement patterns

## Enhanced LLM Request Handler

The enhanced LLM request handler (`OllamaEnhancedService`) provides intelligent parameter management and consistent response formatting.

### Temperature Control

The system automatically sets the appropriate temperature based on the task type:

```python
# For factual tasks (uses temperature=0.3)
summary = await ollama_service.summarize_text(
    text="Content to summarize...",
    max_points=5
)

# For creative tasks (uses temperature=0.7)
flashcards = await ollama_service.generate_flashcards(
    text="Content for flashcards...",
    num_cards=3
)
```

Task types and their temperatures:
- **Factual tasks (0.3)**: Summarization, quiz generation, direct Q&A
- **Creative tasks (0.7)**: Flashcard generation, analogy creation, alternative explanations

The system always uses `top_p=0.95` as specified in the requirements.

### JSON Response Format

All LLM responses are returned in structured JSON format:

```python
structured_response = await ollama_service.generate_structured_completion(
    prompt="Analyze machine learning as a topic",
    prompt_type=PromptType.FACTUAL,
    schema={
        "type": "object",
        "properties": {
            "topic": {"type": "string"},
            "concepts": {"type": "array", "items": {"type": "string"}}
        }
    }
)
```

The system:
- Guides the LLM to produce JSON output
- Extracts valid JSON from free-text responses
- Handles JSON parsing errors gracefully
- Returns structured data for consistent processing

### Prompt Type Classification

Prompt types are classified as:

```python
class PromptType(str, Enum):
    FACTUAL = "factual"   # Temperature = 0.3
    CREATIVE = "creative" # Temperature = 0.7
    DEFAULT = "default"   # Temperature = 0.5
```

You can specify the prompt type explicitly or let the system determine it based on the method called.

## Integration Guide

To integrate these enhanced modules with your application:

1. First, initialize the required services:

```python
from study_coach.services import DatabaseService, OllamaEnhancedService, QADatasetService, PromptType

# Initialize services
db_service = DatabaseService()
ollama_service = OllamaEnhancedService("http://localhost:11434")
qa_service = QADatasetService(db_service, ollama_service)

# Initialize database connections
await db_service.create_indexes()
```

2. Use the QA dataset service to manage your study materials:

```python
# Generate QA pairs for a study material
questions = await qa_service.generate_qa_pairs(
    material_id=material_id,
    num_questions=10,
    question_types=["multiple_choice", "short_answer"],
    difficulty="medium",
    topics=material.topics
)

# Generate adversarial examples
adversarial = await qa_service.generate_adversarial_examples(
    material_id=material_id,
    num_examples=3
)

# Record user feedback
await qa_service.record_question_feedback(
    question_id=question_id,
    user_id=user_id,
    is_correct=is_correct,
    is_helpful=is_helpful
)

# Periodically evaluate and update questions
stats = await qa_service.evaluate_and_update_questions(
    material_id=material_id,
    threshold=0.3
)
```

3. Use the enhanced LLM request handler for appropriate temperature settings:

```python
# For factual tasks
factual_result = await ollama_service.generate_completion(
    prompt="Explain neural networks",
    temperature=0.3,  # Low temperature for factual tasks
    top_p=0.95
)

# For creative tasks
creative_result = await ollama_service.generate_completion(
    prompt="Create an analogy for neural networks",
    temperature=0.7,  # Higher temperature for creative tasks
    top_p=0.95
)
```

4. For more convenient usage, use the specialized methods:

```python
# Generate quiz questions (factual, temperature=0.3)
questions = await ollama_service.generate_quiz_questions(
    text=content,
    num_questions=5
)

# Generate flashcards (creative, temperature=0.7)
flashcards = await ollama_service.generate_flashcards(
    text=content,
    num_cards=5
)

# Generate structured completion (auto-select temperature)
structured = await ollama_service.generate_structured_completion(
    prompt="Analyze this concept",
    prompt_type=PromptType.FACTUAL,
    schema=my_schema
)
```

See the `integration_example.py` file for a complete example of how to integrate these enhanced modules with the study coach bot.

## API Reference

See the class documentation in the source files for detailed API reference information:

- `QADatasetService` in `qa_dataset.py`: Enhanced study dataset management
- `OllamaEnhancedService` in `ollama_enhanced.py`: Enhanced LLM request handler
- `EnhancedQuizQuestion` and other models in `enhanced_models.py`: Enhanced data models

For usage examples, see the demo and integration files in the `examples` directory.
