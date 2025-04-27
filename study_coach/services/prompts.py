"""
Prompt templates for the OwlMind Study Coach services.
"""

from typing import List, Dict, Any, Optional


class SummarizationPrompts:
    """Collection of enhanced prompt templates for document summarization."""
    
    @staticmethod
    def get_document_summary_prompt(text: str, max_points: int = 10, topic_keywords: Optional[List[str]] = None) -> str:
        """
        Generate a prompt for document summarization with strong guidance to prevent hallucinations.
        
        Args:
            text: The document text to summarize
            max_points: Maximum number of bullet points to generate
            topic_keywords: Optional list of expected keywords/topics to guide the summarization
            
        Returns:
            A prompt string for the LLM
        """
        # Include topic guidance if provided
        topic_guidance = ""
        if topic_keywords and len(topic_keywords) > 0:
            topics_str = ", ".join(topic_keywords)
            topic_guidance = f"""
The document appears to be about the following topics: {topics_str}.
Focus your summary on these topics if they appear in the document.
"""

        # Create a prompt that strongly emphasizes staying true to the document content
        prompt = f"""IMPORTANT: You are summarizing a specific academic document. Your task is to create an accurate, factual summary STRICTLY BASED ON THE CONTENT PROVIDED BELOW.

STRICT REQUIREMENTS:
1. ONLY use information explicitly stated in the document provided.
2. DO NOT introduce any external information, examples, or facts not present in the text.
3. DO NOT make assumptions beyond what is stated in the text.
4. If the document covers academic topics like AI, algorithms, mathematics, etc., stay focused on those exact topics.
5. If you're uncertain about any content, exclude it rather than risk inaccuracy.
6. Format your response as {max_points} or fewer clear, concise bullet points.
7. Each bullet point must directly reference specific content from the document.

{topic_guidance}

DOCUMENT TO SUMMARIZE:
'''
{text}
'''

Summary format instructions:
- Provide exactly {max_points} or fewer bullet points (fewer if the document is short).
- Each bullet must be 100 characters or less.
- Each bullet must be factually present in the document.
- Focus on key concepts, definitions, theories, and main points.

Return your response as a JSON array of bullet points:
[
  "Key point 1 directly from document",
  "Key point 2 directly from document",
  "Key point 3 directly from document",
  ...
]
"""

        return prompt

    @staticmethod
    def get_topic_extraction_prompt(text: str) -> str:
        """
        Generate a prompt to extract key topics from document text.
        
        Args:
            text: The document text to analyze
            
        Returns:
            A prompt string for the LLM
        """
        prompt = f"""Extract the main academic subject areas and key topics from this document.
Focus on identifying precise technical terms, concepts, theories, and subject fields.

DOCUMENT TEXT:
'''
{text}
'''

Return a JSON object with two arrays:
1. "subject_areas": General academic fields covered (e.g., "Computer Science", "Machine Learning", "Algorithms")
2. "key_topics": Specific technical terms and concepts (e.g., "Reinforcement Learning", "Markov Decision Processes")

Each array should contain 3-8 entries, focusing on the most prominent topics.
For example:
{{
  "subject_areas": ["Artificial Intelligence", "Computational Logic", "Machine Learning"],
  "key_topics": ["Knowledge Bases", "Propositional Logic", "Modus Ponens", "First-Order Logic", "Markov Decision Processes"]
}}
"""
        return prompt

    @staticmethod
    def get_summary_validation_prompt(summary_points: List[str], original_text: str) -> str:
        """
        Generate a prompt to validate if summary points are present in the original text.
        
        Args:
            summary_points: List of summary bullet points
            original_text: The original document text
            
        Returns:
            A prompt string for the LLM
        """
        points_str = "\n".join([f"{i+1}. {point}" for i, point in enumerate(summary_points)])
        
        prompt = f"""VERIFICATION TASK: Carefully analyze each of the following summary points and determine if they are explicitly supported by the provided document text.

SUMMARY POINTS TO VERIFY:
{points_str}

ORIGINAL DOCUMENT TEXT:
'''
{original_text[:5000]}...
'''

For each summary point, determine:
1. If it is EXPLICITLY supported by content in the document (directly stated or a clear paraphrase)
2. If it contains ANY information not found in the document (hallucination)

Return your analysis as a JSON array of objects:
[
  {{
    "point": "The full text of summary point 1",
    "supported": true/false,
    "reason": "Brief explanation of why it is or isn't supported"
  }},
  ...
]
"""
        return prompt


class QuizPrompts:
    """Collection of enhanced prompt templates for quiz generation."""
    
    @staticmethod
    def get_quiz_generation_prompt(text: str, num_questions: int = 5, 
                                  question_type: str = "multiple_choice",
                                  difficulty: str = "medium",
                                  topics: Optional[List[str]] = None) -> str:
        """
        Generate a prompt for quiz question generation with strong anti-hallucination guidance.
        
        Args:
            text: The document text to base questions on
            num_questions: Number of questions to generate
            question_type: Type of questions (multiple_choice, short_answer)
            difficulty: Difficulty level
            topics: Optional list of topics to focus on
            
        Returns:
            A prompt string for the LLM
        """
        topic_str = ', '.join(topics) if topics else "the material"
        
        prompt = f"""IMPORTANT: Generate {num_questions} {difficulty} {question_type} quiz questions STRICTLY BASED ON the following content.

STRICT REQUIREMENTS:
1. ONLY create questions about information EXPLICITLY stated in the document provided.
2. DO NOT introduce any external information, examples, or facts not in the text.
3. DO NOT make assumptions beyond what is stated in the text.
4. Every question and answer must be directly verifiable from the document content.
5. For multiple-choice questions, all options should be plausible within the context of the document.

DOCUMENT CONTENT:
'''
{text[:8000]}
'''

For each question:
- Create a clear, concise question targeting specific information from the document
- For multiple-choice: provide 4 options with exactly one correct answer
- For short-answer: provide the correct answer as stated in the document
- Include the specific topic from the document this question relates to

Format your response as a JSON array of questions:
[
  {{
    "question": "What is [concept from document]?",
    "type": "{question_type}",
    "options": ["Option A", "Option B", "Option C", "Option D"],  // For multiple-choice only
    "correct_answer": 2,  // 0-based index for multiple-choice, or string for short-answer
    "topic": "The specific topic this relates to",
    "document_reference": "Brief excerpt or location in document that contains this information"
  }},
  // more questions...
]
"""
        return prompt


class DetectionPrompts:
    """Collection of prompts for detecting content types and topics."""
    
    @staticmethod
    def get_topic_detection_prompt(text: str) -> str:
        """
        Generate a prompt to detect the main topics and subject areas in a document.
        
        Args:
            text: The document text to analyze
            
        Returns:
            A prompt string for the LLM
        """
        prompt = f"""Analyze the following document and identify:
1. The general subject areas (e.g., Biology, Computer Science, Literature)
2. Specific key topics covered in the document

DOCUMENT TEXT:
'''
{text[:5000]}...
'''

Return your analysis as a JSON object:
{{
    "subject_areas": ["Subject Area 1", "Subject Area 2"],
    "key_topics": ["Topic 1", "Topic 2", "Topic 3"]
}}

Provide 1-3 subject areas and 3-8 key topics. Be specific but concise.
"""
        return prompt


class FlashcardPrompts:
    """Collection of enhanced prompt templates for flashcard generation."""
    
    @staticmethod
    def get_flashcard_generation_prompt(text: str, num_cards: int = 10, 
                                      topics: Optional[List[str]] = None) -> str:
        """
        Generate a prompt for flashcard generation with strong anti-hallucination guidance.
        
        Args:
            text: The document text to base flashcards on
            num_cards: Number of flashcards to generate
            topics: Optional list of topics to focus on
            
        Returns:
            A prompt string for the LLM
        """
        topic_str = ', '.join(topics) if topics else "the material"
        
        prompt = f"""IMPORTANT: Create {num_cards} highly specific flashcards STRICTLY BASED on this study material content.

STRICT REQUIREMENTS:
1. ONLY extract concepts, terms, definitions, and facts that EXPLICITLY APPEAR in the material below.
2. DO NOT use placeholder variables or generic examples not in the text.
3. Each flashcard must reference SPECIFIC content from the material, not general knowledge.
4. For each concept, provide explanations using information ONLY from the document.
5. Include a document reference that briefly indicates where in the document this information appears.

STUDY MATERIAL CONTENT:
'''
{text[:8000]}
'''

For the front side:
- Ask about specific terms, concepts, processes, or facts found in the material
- Make sure the question can be answered from information in the document

For the back side:
- Provide explanations using ONLY information found in the document
- Do not include any external examples or knowledge not in the document

Format your response as a JSON array:
[
  {{
    "front": "What is [SPECIFIC CONCEPT from the document]?",
    "back": "[EXPLANATION based only on document content]",
    "topic": "[SPECIFIC SUBJECT from the document]",
    "document_reference": "Brief indication of where this appears in the document"
  }},
  // more flashcards...
]
"""
        return prompt


class DetectionPrompts:
    """Collection of prompts for hallucination detection."""
    
    @staticmethod
    def get_hallucination_detection_prompt(generated_text: str, source_text: str) -> str:
        """
        Generate a prompt to detect hallucinations in generated content.
        
        Args:
            generated_text: The text to check for hallucinations
            source_text: The source document text
            
        Returns:
            A prompt string for the LLM
        """
        prompt = f"""IMPORTANT: Determine if the generated content contains any hallucinations (information not present in the source document).

GENERATED CONTENT:
'''
{generated_text}
'''

SOURCE DOCUMENT:
'''
{source_text[:6000]}
'''

Carefully analyze the generated content and identify any statements that:
1. Contain information not found in the source document
2. Make claims that cannot be verified from the source document
3. Include examples, statistics, or concepts not mentioned in the source

Return your analysis as a JSON object:
{{
  "contains_hallucinations": true/false,
  "hallucinations": [
    {{
      "text": "The specific hallucinated statement",
      "reason": "Explanation of why this is a hallucination"
    }},
    // more if found...
  ],
  "confidence": 0-100  // Your confidence level in this assessment
}}
"""
        return prompt
