"""
Service for managing the QA dataset with feedback handling and adversarial examples.
"""

import datetime
import json
import uuid
from typing import List, Dict, Any, Optional, Union, Tuple
import motor.motor_asyncio
from ..models.models import QuizQuestion, DifficultyLevel, StudyMaterial


class QADatasetService:
    """
    Service for enhancing study datasets with automated QA generation,
    feedback handling, and adversarial examples.
    """

    def __init__(self, db_service, ollama_service):
        """Initialize the QA dataset service."""
        self.db = db_service
        self.ollama = ollama_service
        self.db_client = self.db.client
        self.qa_db = self.db_client.study_coach
        
        # Collections
        self.questions = self.qa_db.questions
        self.feedback = self.qa_db.question_feedback
        self.changelog = self.qa_db.qa_changelog

    async def generate_qa_pairs(
        self, 
        material_id: str,
        num_questions: int = 10,
        question_types: List[str] = ["multiple_choice", "short_answer"],
        difficulty: str = "medium",
        topics: List[str] = None,
    ) -> List[QuizQuestion]:
        """
        Generate QA pairs from study material content.
        
        Args:
            material_id: ID of the study material
            num_questions: Number of questions to generate
            question_types: Types of questions to generate
            difficulty: Difficulty level
            topics: Specific topics to focus on
        
        Returns:
            List of generated QuizQuestion objects
        """
        # Get the study material content
        material = await self.db.get_material_by_id(material_id)
        if not material:
            raise ValueError(f"Study material with ID {material_id} not found")
        
        # Get the content based on content_type
        content = await self._get_material_content(material)
        if not content:
            raise ValueError(f"Could not retrieve content for material {material_id}")
        
        # Determine distribution of question types
        qtype_count = {qt: num_questions // len(question_types) for qt in question_types}
        remainder = num_questions % len(question_types)
        for i, qt in enumerate(question_types):
            if i < remainder:
                qtype_count[qt] += 1
        
        all_questions = []
        
        # Generate questions for each question type
        for q_type, count in qtype_count.items():
            if count <= 0:
                continue
                
            # Generate questions - use temperature=0.3 for factual questions
            questions = await self.ollama.generate_quiz_questions(
                text=content,
                num_questions=count,
                question_type=q_type,
                model="llama2:7b",  # Default model
                difficulty=difficulty,
                topics=topics
            )
            
            # Convert to QuizQuestion objects
            for q in questions:
                question_id = str(uuid.uuid4())
                quiz_question = QuizQuestion(
                    id=question_id,
                    material_id=material_id,
                    question=q.get("question", ""),
                    question_type=q.get("type", q_type),
                    options=q.get("options", []) if q_type == "multiple_choice" else [],
                    correct_answer=q.get("correct_answer"),
                    topic=q.get("topic", "General"),
                    difficulty=DifficultyLevel(difficulty),
                    created_at=datetime.datetime.now()
                )
                
                # Document the creation in the changelog
                await self._log_qa_change(
                    question_id=question_id,
                    material_id=material_id,
                    action="created",
                    details="Automatically generated QA pair",
                    qa_data=quiz_question.to_dict()
                )
                
                all_questions.append(quiz_question)
        
        # Save all questions to the database
        if all_questions:
            await self.db.create_questions_batch(all_questions)
            
        return all_questions

    async def generate_adversarial_examples(
        self,
        material_id: str,
        num_examples: int = 3,
        base_on_existing: bool = True
    ) -> List[QuizQuestion]:
        """
        Generate challenging adversarial examples that test the boundaries
        of understanding and are intentionally tricky.
        
        Args:
            material_id: ID of the study material
            num_examples: Number of adversarial examples to generate
            base_on_existing: Whether to base the adversaries on existing questions
            
        Returns:
            List of generated adversarial QuizQuestion objects
        """
        # Get the study material content
        material = await self.db.get_material_by_id(material_id)
        if not material:
            raise ValueError(f"Study material with ID {material_id} not found")
        
        # Get content
        content = await self._get_material_content(material)
        if not content:
            raise ValueError(f"Could not retrieve content for material {material_id}")
        
        existing_questions = []
        if base_on_existing:
            # Get existing questions for this material
            cursor = self.questions.find({"material_id": material_id})
            async for doc in cursor:
                existing_questions.append(QuizQuestion.from_dict(doc))
            
            # If no existing questions, we can't base on them
            if not existing_questions:
                base_on_existing = False
        
        # Prepare prompt based on whether we're using existing questions
        if base_on_existing and existing_questions:
            # Select a sample of existing questions to base adversaries on
            sample_size = min(5, len(existing_questions))
            sample_questions = existing_questions[:sample_size]  # Use first few for simplicity
            
            # Format sample questions for the prompt
            sample_text = ""
            for i, q in enumerate(sample_questions):
                if q.question_type == "multiple_choice":
                    options_text = "\n".join([f"    - {opt}" for opt in q.options])
                    answer = q.options[q.correct_answer] if isinstance(q.correct_answer, int) and q.correct_answer < len(q.options) else "Unknown"
                    sample_text += f"Question {i+1}: {q.question}\nOptions:\n{options_text}\nCorrect answer: {answer}\n\n"
                else:
                    sample_text += f"Question {i+1}: {q.question}\nAnswer: {q.correct_answer}\n\n"
            
            prompt = f"""Create {num_examples} CHALLENGING and TRICKY adversarial examples based on this material, 
similar to but more difficult than these existing questions:

{sample_text}

Study material content:
{content[:4000]}

For each adversarial example:
1. Design a question that tests deeper understanding, includes common misconceptions, or has subtle nuances
2. Create questions that appear straightforward but require careful analysis
3. For multiple-choice: include plausible distractors that represent common errors in reasoning
4. For short-answer: require precision in the answer that tests exact understanding

Format your response as a JSON array of questions:
[
  {{
    "question": "The tricky or challenging question that tests limits of understanding",
    "type": "multiple_choice", 
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": 2,  // 0-based index for multiple-choice, or string for short-answer
    "topic": "The specific topic this relates to",
    "adversarial_type": "misconception" // e.g., "misconception", "edge_case", "precision", "ambiguity"
  }}
]
"""
        else:
            # Create adversarial questions from scratch
            prompt = f"""Create {num_examples} CHALLENGING and TRICKY adversarial examples based on this study material content:

{content[:4000]}

For each adversarial example:
1. Design a question that tests deeper understanding, includes common misconceptions, or has subtle nuances
2. Create questions that appear straightforward but require careful analysis 
3. For multiple-choice: include plausible distractors that represent common errors in reasoning
4. For short-answer: require precision in the answer that tests exact understanding

Format your response as a JSON array of questions:
[
  {{
    "question": "The tricky or challenging question that tests limits of understanding",
    "type": "multiple_choice", 
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": 2,  // 0-based index for multiple-choice, or string for short-answer
    "topic": "The specific topic this relates to",
    "adversarial_type": "misconception" // e.g., "misconception", "edge_case", "precision", "ambiguity"
  }}
]
"""

        # Generate the adversarial examples - use temperature=0.7 for more creative outputs
        response = await self.ollama.generate_completion(
            prompt=prompt,
            model="llama2:7b",  # Default model
            temperature=0.7,  # Creative tasks need higher temperature
            top_p=0.95,
            max_tokens=2000
        )
        
        # Parse the JSON response
        adversarial_questions = []
        try:
            # Find JSON array in the response
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                examples = json.loads(json_str)
                
                # Convert to QuizQuestion objects and save
                for ex in examples:
                    question_id = str(uuid.uuid4())
                    question = QuizQuestion(
                        id=question_id,
                        material_id=material_id,
                        question=ex.get("question", ""),
                        question_type=ex.get("type", "multiple_choice"),
                        options=ex.get("options", []),
                        correct_answer=ex.get("correct_answer"),
                        topic=ex.get("topic", "Adversarial example"),
                        difficulty=DifficultyLevel.HARD,  # Adversarial examples are always hard
                        created_at=datetime.datetime.now()
                    )
                    
                    # Add adversarial metadata as additional field in the database
                    question_dict = question.to_dict()
                    question_dict["is_adversarial"] = True
                    question_dict["adversarial_type"] = ex.get("adversarial_type", "general")
                    
                    # Log the creation
                    await self._log_qa_change(
                        question_id=question_id,
                        material_id=material_id,
                        action="created",
                        details="Generated adversarial example",
                        qa_data=question_dict
                    )
                    
                    adversarial_questions.append(question)
        except Exception as e:
            print(f"Error parsing adversarial examples: {str(e)}")
            return []
        
        # Save adversarial questions to database
        if adversarial_questions:
            # For each question, save with the additional metadata
            for q in adversarial_questions:
                q_dict = q.to_dict()
                q_dict["is_adversarial"] = True
                await self.questions.insert_one(q_dict)
        
        return adversarial_questions

    async def record_question_feedback(
        self, 
        question_id: str,
        user_id: str,
        is_correct: bool,
        is_helpful: Optional[bool] = None,
        difficulty_rating: Optional[int] = None,
        feedback_text: Optional[str] = None
    ) -> str:
        """
        Record user feedback on a question.
        
        Args:
            question_id: ID of the question
            user_id: ID of the user providing feedback
            is_correct: Whether the user answered correctly
            is_helpful: Whether the user found the question helpful
            difficulty_rating: User rating of difficulty (1-5)
            feedback_text: Optional text feedback
            
        Returns:
            ID of the feedback record
        """
        feedback_id = str(uuid.uuid4())
        
        # Create feedback record
        feedback_data = {
            "id": feedback_id,
            "question_id": question_id,
            "user_id": user_id,
            "is_correct": is_correct,
            "is_helpful": is_helpful,
            "difficulty_rating": difficulty_rating,
            "feedback_text": feedback_text,
            "created_at": datetime.datetime.now()
        }
        
        # Insert feedback record
        await self.feedback.insert_one(feedback_data)
        
        # Update quality metrics for the question
        await self._update_question_quality_metrics(question_id)
        
        return feedback_id

    async def evaluate_and_update_questions(self, material_id: str, threshold: float = 0.3) -> Dict[str, Any]:
        """
        Evaluate questions for a study material and update or remove low-quality ones.
        
        Args:
            material_id: ID of the study material
            threshold: Quality threshold below which questions are removed/updated
            
        Returns:
            Summary of updates made
        """
        # Get all questions for this material
        cursor = self.questions.find({"material_id": material_id})
        questions = []
        async for doc in cursor:
            questions.append(doc)
        
        # Get feedback for all questions
        all_feedback = {}
        for q in questions:
            q_id = q["id"]
            feedback_cursor = self.feedback.find({"question_id": q_id})
            q_feedback = []
            async for f in feedback_cursor:
                q_feedback.append(f)
            all_feedback[q_id] = q_feedback
        
        # Stats to return
        stats = {
            "total_questions": len(questions),
            "removed": 0,
            "updated": 0,
            "no_action": 0
        }
        
        # Process each question
        for q in questions:
            q_id = q["id"]
            feedback = all_feedback.get(q_id, [])
            
            if not feedback:
                stats["no_action"] += 1
                continue
            
            # Calculate metrics
            total_attempts = len(feedback)
            correct_answers = sum(1 for f in feedback if f.get("is_correct", False))
            helpful_ratings = [f.get("is_helpful") for f in feedback if f.get("is_helpful") is not None]
            helpful_count = sum(1 for h in helpful_ratings if h)
            
            # Calculate quality score
            accuracy = correct_answers / total_attempts if total_attempts else 0
            helpfulness = helpful_count / len(helpful_ratings) if helpful_ratings else 0
            
            # Balance accuracy and helpfulness (low accuracy might mean it's a good challenging question)
            quality_score = (accuracy * 0.4) + (helpfulness * 0.6)
            
            # Decide action based on quality score
            if quality_score < threshold:
                if helpfulness < 0.2:  # Very unhelpful questions should be removed
                    # Remove the question
                    await self.questions.delete_one({"id": q_id})
                    
                    # Log the removal
                    await self._log_qa_change(
                        question_id=q_id,
                        material_id=material_id,
                        action="removed",
                        details=f"Removed due to low quality score ({quality_score:.2f})",
                        qa_data=q
                    )
                    
                    stats["removed"] += 1
                else:
                    # Try to improve the question
                    improved = await self._improve_question(q, material_id, feedback)
                    if improved:
                        stats["updated"] += 1
                    else:
                        stats["no_action"] += 1
            else:
                stats["no_action"] += 1
        
        return stats

    async def _improve_question(self, question: Dict[str, Any], material_id: str, feedback: List[Dict[str, Any]]) -> bool:
        """
        Attempt to improve a question based on feedback.
        
        Args:
            question: The question to improve
            material_id: ID of the study material
            feedback: List of feedback records for this question
            
        Returns:
            Whether the question was successfully improved
        """
        # Get the study material content for context
        material = await self.db.get_material_by_id(material_id)
        if not material:
            return False
            
        content = await self._get_material_content(material)
        if not content:
            return False
        
        # Summarize feedback
        feedback_summary = []
        for f in feedback:
            summary = f"User rated: correct={f.get('is_correct', 'unknown')}, helpful={f.get('is_helpful', 'unknown')}"
            if f.get("feedback_text"):
                summary += f", comment: '{f.get('feedback_text')}'"
            feedback_summary.append(summary)
        
        # Create prompt for improvement
        prompt = f"""Improve this quiz question based on user feedback and the study material content.

Current Question: {question.get('question')}
Question Type: {question.get('question_type')}

"""
        
        if question.get('question_type') == 'multiple_choice':
            options = question.get('options', [])
            options_text = "\n".join([f"- {opt}" for opt in options])
            correct_idx = question.get('correct_answer', 0)
            correct_answer = options[correct_idx] if isinstance(correct_idx, int) and correct_idx < len(options) else "Unknown"
            
            prompt += f"""Options:
{options_text}
Correct Answer: {correct_answer}

"""
        else:
            prompt += f"""Correct Answer: {question.get('correct_answer', 'Unknown')}

"""
        
        prompt += f"""User Feedback:
{chr(10).join(feedback_summary)}

Relevant Content from Study Material:
{content[:2000]}

Create an improved version of this question that addresses any issues shown in the feedback.
Maintain the same question type ({question.get('question_type')}) but make it clearer, more precise, or better aligned with the study material.

Format your response as JSON:
{{
    "question": "The improved question text",
    "type": "{question.get('question_type')}",
    "options": ["Option A", "Option B", "Option C", "Option D"],  // Only for multiple-choice
    "correct_answer": 2,  // 0-based index for multiple-choice or string for short-answer
    "topic": "The specific topic",
    "improvement_notes": "Brief explanation of what was improved"
}}
"""
        
        # Generate improved question
        response = await self.ollama.generate_completion(
            prompt=prompt,
            model="llama2:7b",
            temperature=0.7,  # Creative task
            top_p=0.95,
            max_tokens=1000
        )
        
        try:
            # Find JSON object in the response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                improved = json.loads(json_str)
                
                # Update the question
                update_data = {
                    "question": improved.get("question", question.get("question")),
                    "topic": improved.get("topic", question.get("topic")),
                    "updated_at": datetime.datetime.now(),
                    "improvement_notes": improved.get("improvement_notes", "Question automatically improved")
                }
                
                if question.get('question_type') == 'multiple_choice' and "options" in improved:
                    update_data["options"] = improved.get("options")
                    
                if "correct_answer" in improved:
                    update_data["correct_answer"] = improved.get("correct_answer")
                
                # Apply the update
                await self.questions.update_one(
                    {"id": question.get("id")},
                    {"$set": update_data}
                )
                
                # Log the change
                original_data = question.copy()
                updated_data = {**question, **update_data}
                
                await self._log_qa_change(
                    question_id=question.get("id"),
                    material_id=material_id,
                    action="updated",
                    details=improved.get("improvement_notes", "Question automatically improved"),
                    qa_data=updated_data,
                    previous_data=original_data
                )
                
                return True
                
        except Exception as e:
            print(f"Error improving question {question.get('id')}: {str(e)}")
            return False
            
        return False

    async def _get_material_content(self, material: StudyMaterial) -> str:
        """
        Helper method to get the content of a study material.
        
        Args:
            material: The StudyMaterial object
            
        Returns:
            The text content of the material
        """
        # This is a placeholder - in a real implementation, you would:
        # 1. Check content_type (pdf, text, url)
        # 2. Load the content accordingly
        # For now, we'll assume it's stored elsewhere and return a placeholder
        
        # In a real implementation, you might:
        # if material.content_type == "pdf":
        #     return self._extract_pdf_content(material.content_path)
        # elif material.content_type == "url":
        #     return self._fetch_url_content(material.url)
        
        # For now, just return a placeholder - replace this with actual content retrieval
        return "Sample study material content for placeholder purposes. Replace this with actual content retrieval logic."

    async def _update_question_quality_metrics(self, question_id: str) -> None:
        """
        Update quality metrics for a question based on accumulated feedback.
        
        Args:
            question_id: ID of the question
        """
        # Get all feedback for this question
        cursor = self.feedback.find({"question_id": question_id})
        feedback = []
        async for doc in cursor:
            feedback.append(doc)
        
        if not feedback:
            return
            
        # Calculate metrics
        total_attempts = len(feedback)
        correct_answers = sum(1 for f in feedback if f.get("is_correct", False))
        helpful_ratings = [f.get("is_helpful") for f in feedback if f.get("is_helpful") is not None]
        helpful_count = sum(1 for h in helpful_ratings if h)
        
        # Calculate quality metrics
        accuracy = correct_answers / total_attempts if total_attempts else 0
        helpfulness = helpful_count / len(helpful_ratings) if helpful_ratings else 0
        
        # Update the question record with the new metrics
        update_data = {
            "quality_metrics": {
                "accuracy": accuracy,
                "helpfulness": helpfulness,
                "total_attempts": total_attempts,
                "updated_at": datetime.datetime.now()
            }
        }
        
        await self.questions.update_one(
            {"id": question_id},
            {"$set": update_data}
        )

    async def _log_qa_change(
        self,
        question_id: str,
        material_id: str,
        action: str,
        details: str,
        qa_data: Dict[str, Any],
        previous_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log changes to questions for audit and history tracking.
        
        Args:
            question_id: ID of the question
            material_id: ID of the study material
            action: Action taken (created, updated, removed)
            details: Description of the change
            qa_data: Current question data
            previous_data: Previous question data (for updates)
            
        Returns:
            ID of the changelog entry
        """
        log_id = str(uuid.uuid4())
        
        log_entry = {
            "id": log_id,
            "question_id": question_id,
            "material_id": material_id,
            "action": action,
            "details": details,
            "timestamp": datetime.datetime.now(),
            "qa_data": qa_data,
        }
        
        if previous_data:
            log_entry["previous_data"] = previous_data
            
        await self.changelog.insert_one(log_entry)
        return log_id
