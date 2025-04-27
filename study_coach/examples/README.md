# Enhanced Study Dataset and LLM Request Handler

This module enhances the study dataset and improves the LLM request handler for the OwlMind Study Coach.

## Features

### Enhanced Study Dataset

- **Automated QA Generation**: Automatically generates question-answer pairs from study materials.
- **User Feedback Capture**: Records user feedback on each QA pair (correct/incorrect, helpful/unhelpful).
- **Quality Control**: Updates or removes low-quality QAs based on accumulated feedback.
- **Adversarial Examples**: Adds tricky or challenging questions to test student understanding and model robustness.
- **Comprehensive Change Logs**: Maintains complete history of all dataset changes in MongoDB.

### Improved LLM Request Handler

- **Content-Type Aware Temperature Setting**:
  - Temperature = 0.3 for factual tasks (summaries, direct answers, quizzes)
  - Temperature = 0.7 for creative tasks (flashcard generation, alternative explanations)
  - Consistent top_p = 0.95 for all completions
  
- **Automatic Temperature Selection**: The system automatically selects the appropriate temperature based on the prompt type.
  
- **Structured JSON Responses**: All LLM responses are structured in JSON format for consistent parsing.

## Usage

### Example: Generate QA Pairs

```python
from study_coach.services import QADatasetService

# Generate questions
questions = await qa_service.generate_qa_pairs(
    material_id="material-id-123",
    num_questions=5,
    question_types=["multiple_choice", "short_answer"],
    difficulty="medium",
    topics=["Physics", "Mechanics"]
)
```

### Example: Generate Adversarial Questions

```python
adversarial_questions = await qa_service.generate_adversarial_examples(
    material_id="material-id-123",
    num_examples=3,
    base_on_existing=True  # Generate adversarial examples based on existing questions
)
```

### Example: Record User Feedback

```python
feedback_id = await qa_service.record_question_feedback(
    question_id="question-id-123",
    user_id="user-id-456",
    is_correct=True,
    is_helpful=True,
    difficulty_rating=3,  # 1-5 scale
    feedback_text="This was a clear and helpful question!"
)
```

### Example: LLM Request with Appropriate Temperature

```python
from study_coach.services import OllamaEnhancedService, PromptType

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

# With structured JSON output
schema = {
    "type": "object",
    "properties": {
        "topic": {"type": "string"},
        "concepts": {"type": "array", "items": {"type": "string"}}
    }
}

structured_response = await ollama_service.generate_structured_completion(
    prompt="Analyze machine learning as a topic and list key concepts",
    prompt_type=PromptType.FACTUAL,
    schema=schema,
    max_tokens=500
)
```

## Running the Demo

Execute the demo script to see the enhanced features in action:

```
python -m study_coach.examples.enhanced_qa_demo
```
