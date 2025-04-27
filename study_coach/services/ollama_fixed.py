"""
Service for interacting with the Ollama API for AI capabilities.
"""

import json
import asyncio
import httpx
import re
import ast
from typing import List, Dict, Any, Optional, Union, Tuple


class OllamaService:
    """Service for interacting with the Ollama API."""
    def __init__(self, base_url: str = "http://localhost:11434"):
        """Initialize the Ollama service."""
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=180.0)  # Increased timeout for generation (3 minutes)
        
    async def generate_completion(
        self, 
        prompt: str, 
        model: str = "llama2:7b", 
        temperature: float = 0.7,
        top_p: float = 0.95,
        max_tokens: int = 500
    ) -> str:
        """Generate a text completion using Ollama."""
        url = f"{self.base_url}/api/generate"
        
        data = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        try:
            response = await self.client.post(url, json=data)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
        except httpx.ReadTimeout:
            print(f"Timeout error when calling Ollama API: {url}")
            raise  # Re-raise so callers can handle it
        except httpx.HTTPStatusError as e:
            print(f"HTTP error when calling Ollama API: {e.response.status_code} {e.response.reason_phrase}")
            # Check if model not found
            if e.response.status_code == 404:
                available_models = await self.list_available_models()
                print(f"Available models: {available_models}")
                raise ValueError(f"Model '{model}' not found. Available models: {available_models}")
            raise
        except Exception as e:
            print(f"Unexpected error when calling Ollama API: {type(e).__name__}: {str(e)}")
            raise
    
    async def generate_embeddings(self, text: str, model: str = "all-minilm") -> List[float]:
        """Generate embeddings for text using Ollama."""
        url = f"{self.base_url}/api/embeddings"
        
        data = {
            "model": model,
            "prompt": text
        }
        
        response = await self.client.post(url, json=data)
        response.raise_for_status()
        
        result = response.json()
        return result.get("embedding", [])
    
    async def list_available_models(self) -> List[str]:
        """Get a list of available models from Ollama."""
        url = f"{self.base_url}/api/tags"
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            
            result = response.json()
            models = [model.get("name") for model in result.get("models", [])]
            return models
        except Exception as e:
            print(f"Error getting available models: {type(e).__name__}: {str(e)}")
            return []
    
    async def summarize_text(
        self, 
        text: str, 
        model: str = "llama2:7b",
        max_points: int = 10
    ) -> List[str]:
        """Summarize text into bullet points."""
        # Limit text size to avoid timeouts
        if len(text) > 12000:
            text = text[:12000] + "..."
        
        prompt = f"""Summarize the following text into {max_points} or fewer clear, concise bullet points
that capture the most important information. Focus on key concepts, facts, and main ideas.
Keep each bullet point under 100 characters for readability.

{text}

Format your response as a JSON array of bullet points:
"""
        
        try:
            response = await self.generate_completion(
                prompt=prompt,
                model=model,
                temperature=0.3,
                max_tokens=1000
            )
        except httpx.ReadTimeout:
            print("Timeout when generating summary, falling back to simpler approach")
            # If we get a timeout, try with a shorter chunk of text
            short_text = text[:6000] + "..." if len(text) > 6000 else text
            try:
                # Try again with shorter text and simpler prompt
                simple_prompt = f"Summarize this in {max_points} bullet points: {short_text}"
                response = await self.generate_completion(
                    prompt=simple_prompt,
                    model=model,
                    temperature=0.3,
                    max_tokens=500
                )
            except Exception as e:
                print(f"Error in summary fallback: {type(e).__name__}: {str(e)}")
                # Return a simple fallback
                return ["Failed to generate summary due to timeout. Try with a shorter document."]
        except Exception as e:
            print(f"Error in summarize_text: {type(e).__name__}: {str(e)}")
            return [f"Error generating summary: {type(e).__name__}: {str(e)}"]
        
        # Extract JSON array from the response
        try:
            # Try to find JSON array in the response
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                bullets = json.loads(json_str)
                
                # Ensure total length of bullets is under Discord's limit (1024 chars)
                total_length = 0
                truncated_bullets = []
                for bullet in bullets:
                    # Truncate individual bullet points if they're too long
                    if len(bullet) > 100:
                        bullet = bullet[:97] + "..."
                    
                    # Add bullet point if it doesn't exceed Discord's limit
                    if total_length + len(bullet) + 2 <= 1000:  # +2 for bullet point formatting
                        truncated_bullets.append(bullet)
                        total_length += len(bullet) + 2
                    else:
                        break
                
                return truncated_bullets
            
            # Fallback: split by newlines and clean up
            bullets = [line.strip().replace('• ', '').replace('- ', '') 
                      for line in response.split('\n') 
                      if line.strip() and (line.strip().startswith('•') or line.strip().startswith('-'))]
            
            # Ensure total length is under Discord's limit
            total_length = 0
            truncated_bullets = []
            for bullet in bullets[:max_points]:
                # Truncate individual bullet points if they're too long
                if len(bullet) > 100:
                    bullet = bullet[:97] + "..."
                
                # Add bullet point if it doesn't exceed Discord's limit
                if total_length + len(bullet) + 2 <= 1000:  # +2 for bullet point formatting
                    truncated_bullets.append(bullet)
                    total_length += len(bullet) + 2
                else:
                    break
            
            return truncated_bullets
        except:
            # If JSON parsing fails, just return a truncated version of the raw text
            if len(response) > 1000:
                return [response[:997] + "..."]
            return [response]
    
    async def generate_quiz_questions(
        self,
        text: str,
        num_questions: int = 5,
        question_type: str = "multiple_choice",
        model: str = "llama2:7b",
        difficulty: str = "medium",
        topics: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Generate quiz questions based on text content."""
        # Limit text size to avoid timeouts
        if len(text) > 12000:
            text = text[:12000] + "..."
            
        topic_str = ', '.join(topics) if topics else "the material"
        
        prompt = f"""Generate {num_questions} {difficulty} {question_type} quiz questions about {topic_str} based on this content:

{text[:8000]}

For each question:
- Create a clear, concise question
- For multiple-choice: provide 4 options with exactly one correct answer
- For short-answer: provide the correct answer
- Include the question topic

Format your response as a JSON array of questions:
[
  {{
    "question": "What is the main concept?",
    "type": "multiple_choice",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": 2,  // 0-based index for multiple-choice, or string for short-answer
    "topic": "The specific topic this relates to"
  }},
  // more questions...
]
"""
        
        try:
            response = await self.generate_completion(
                prompt=prompt,
                model=model,
                temperature=0.7,
                max_tokens=2000
            )
        except httpx.ReadTimeout:
            print("Timeout when generating quiz questions, trying with shorter text")
            short_text = text[:4000] + "..." if len(text) > 4000 else text
            try:
                simple_prompt = f"""Generate {num_questions} simple {question_type} questions about: {short_text}"""
                response = await self.generate_completion(
                    prompt=simple_prompt,
                    model=model, 
                    temperature=0.7,
                    max_tokens=1000
                )
            except Exception as e:
                print(f"Error in quiz fallback: {type(e).__name__}: {str(e)}")
                return [{"question": "Quiz generation failed due to timeout. Try with shorter content.",
                        "type": question_type,
                        "options": ["Try again", "Use shorter text", "Different model", "Contact support"],
                        "correct_answer": 0,
                        "topic": "Error"}]
        except Exception as e:
            print(f"Error generating quiz questions: {type(e).__name__}: {str(e)}")
            return [{"question": f"Error: {str(e)}",
                    "type": question_type,
                    "options": ["Try again", "Use shorter text", "Different model", "Contact support"],
                    "correct_answer": 0,
                    "topic": "Error"}]
        
        # Extract JSON array from the response
        try:
            # Try to find JSON array in the response
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                
                # Clean up JSON string to remove comments and trailing commas
                json_str = re.sub(r'//.*', '', json_str)  # Remove // comments
                json_str = re.sub(r',(\s*[\]}])', r'\1', json_str)  # Remove trailing commas
                
                try:
                    questions = json.loads(json_str)
                    
                    # Validate the structure of each question
                    validated_questions = []
                    for q in questions:
                        if "question" in q:
                            # Ensure required fields exist
                            if question_type == "multiple_choice" and ("options" not in q or "correct_answer" not in q):
                                q["options"] = q.get("options") or ["Option A", "Option B", "Option C", "Option D"]
                                q["correct_answer"] = q.get("correct_answer", 0)
                            elif question_type == "short_answer" and "correct_answer" not in q:
                                q["correct_answer"] = "No answer provided"
                                
                            q["type"] = q.get("type", question_type)
                            q["topic"] = q.get("topic", "General")
                            validated_questions.append(q)
                    
                    return validated_questions[:num_questions]
                except json.JSONDecodeError as e:
                    print(f"JSON parsing error: {str(e)}")
                    print(f"JSON string: {json_str[:100]}...")
                    
                    # Try a more aggressive cleanup
                    try:
                        # Remove any non-JSON syntax and hope for the best
                        # Convert single quotes to double quotes
                        json_str = json_str.replace("'", '"')
                        # Try to parse with ast first (more forgiving)
                        parsed = ast.literal_eval(json_str)
                        # Convert to proper JSON
                        cleaned_json = json.dumps(parsed)
                        questions = json.loads(cleaned_json)
                        return questions[:num_questions]
                    except Exception as e2:
                        print(f"Secondary parsing error: {str(e2)}")
                        # Create a fallback question
                        return [{"question": "Quiz generation failed. Please try again with shorter content.",
                                "type": question_type,
                                "options": ["Try again", "Use shorter text", "Different model", "Contact support"],
                                "correct_answer": 0,
                                "topic": "Error"}]
            
            # Try to parse questions in a non-JSON format
            questions = []
            lines = response.split('\n')
            current_question = None
            
            for i, line in enumerate(lines):
                if re.match(r'^\d+[\.\)]', line):  # Line starts with a number followed by . or )
                    # Save previous question if exists
                    if current_question and "question" in current_question:
                        questions.append(current_question)
                    
                    # Start new question
                    question_text = re.sub(r'^\d+[\.\)]', '', line).strip()
                    current_question = {
                        "question": question_text,
                        "type": question_type,
                        "topic": "Extracted from text"
                    }
                    
                    # Look ahead for options
                    if question_type == "multiple_choice":
                        options = []
                        correct_idx = 0
                        for j in range(1, 5):
                            if i + j < len(lines) and re.match(r'^[A-Da-d][\.\)]', lines[i + j]):
                                option_text = re.sub(r'^[A-Da-d][\.\)]', '', lines[i + j]).strip()
                                # Check if this option is marked as correct
                                if "*" in option_text or "correct" in option_text.lower():
                                    correct_idx = j - 1
                                    option_text = option_text.replace("*", "").replace("(correct)", "").strip()
                                options.append(option_text)
                        
                        if len(options) > 0:
                            current_question["options"] = options
                            current_question["correct_answer"] = correct_idx
                    
                elif current_question and "answer" in line.lower() and ":" in line:
                    current_question["correct_answer"] = line.split(":", 1)[1].strip()
            
            # Add the last question
            if current_question and "question" in current_question:
                questions.append(current_question)
            
            if questions:
                return questions[:num_questions]
                
            # If we still couldn't parse anything useful
            return [{"question": "Quiz generation failed. Please try again.",
                    "type": question_type,
                    "options": ["Try again", "Use shorter text", "Different model", "Contact support"],
                    "correct_answer": 0,
                    "topic": "Error"}]
        except Exception as e:
            print(f"Error parsing quiz questions: {type(e).__name__}: {str(e)}")
            return [{"question": f"Error: {str(e)}",
                    "type": question_type,
                    "options": ["Try again", "Use shorter text", "Different model", "Contact support"],
                    "correct_answer": 0,
                    "topic": "Error"}]
    
    async def generate_flashcards(
        self,
        text: str,
        num_cards: int = 10,
        model: str = "llama2:7b",
        topics: List[str] = None
    ) -> List[Dict[str, str]]:
        """Generate flashcards based on text content."""
        # Limit text size to avoid timeouts
        if len(text) > 12000:
            text = text[:12000] + "..."
            
        topic_str = ', '.join(topics) if topics else "the material"
        
        prompt = f"""Generate {num_cards} highly specific flashcards based DIRECTLY on this study material content:

{text[:8000]}

IMPORTANT INSTRUCTIONS:
1. Extract REAL concepts, terms, definitions, and key facts that appear in the material above.
2. DO NOT use placeholder variables (X, Y, Z) - use actual terms from the text.
3. Each flashcard must reference specific content from the material, not generic concepts.
4. For each concept, provide COMPLETE explanations, never ending with "...".
5. Be precise and educational - these are for actual studying.

For the front side:
- Ask about specific terms, concepts, processes, or facts found in the material
- Frame questions to test understanding, not just recall
- Include enough context for the question to make sense

For the back side:
- Provide COMPLETE explanations (never truncated with "...")
- Include supporting details from the material
- If appropriate, include examples or applications

For the topic:
- Use the exact subject area from the material (not "General" or "Specific field")
- Be specific: e.g., "Neural Networks in Deep Learning" instead of just "AI"

Format your response as a JSON array:
[
  {{
    "front": "What is [SPECIFIC CONCEPT] as described in the material?",
    "back": "[COMPLETE EXPLANATION with details from the text]",
    "topic": "[SPECIFIC SUBJECT from the material]"
  }},
  // more flashcards with REAL content from the material...
]
"""
        
        try:
            response = await self.generate_completion(
                prompt=prompt,
                model=model,
                temperature=0.7,
                max_tokens=2000
            )
        except httpx.ReadTimeout:
            print("Timeout when generating flashcards, trying with shorter text")
            short_text = text[:4000] + "..." if len(text) > 4000 else text
            try:
                simple_prompt = f"""Create {num_cards} specific flashcards from this study material:

{short_text}

RULES:
1. Use ONLY real concepts from the material above
2. NO placeholder terms like X, Y, Z - use actual terms
3. Provide COMPLETE answers (no "...")
4. Include specific topics from the material

Format as:
[
  {{
    "front": "[SPECIFIC question about real content]",
    "back": "[COMPLETE explanation with details]",
    "topic": "[SPECIFIC subject from the text]"
  }}
]"""
                response = await self.generate_completion(
                    prompt=simple_prompt,
                    model=model,
                    temperature=0.7, 
                    max_tokens=1000
                )
            except Exception as e:
                print(f"Error in flashcards fallback: {type(e).__name__}: {str(e)}")
                return [{"front": "Flashcard generation failed due to timeout", 
                        "back": "Try again with shorter content",
                        "topic": "Error"}]
        except Exception as e:
            print(f"Error generating flashcards: {type(e).__name__}: {str(e)}")
            return [{"front": f"Error generating flashcards", 
                    "back": f"Error: {str(e)}",
                    "topic": "Error"}]
        
        # Extract JSON array from the response
        try:
            # Try to find JSON array in the response
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                
                # Clean up JSON string to remove comments and trailing commas
                json_str = re.sub(r'//.*', '', json_str)  # Remove // comments
                json_str = re.sub(r',(\s*[\]}])', r'\1', json_str)  # Remove trailing commas
                
                try:
                    flashcards = json.loads(json_str)
                    
                    # Validate the structure of each flashcard
                    validated_cards = []
                    for card in flashcards:
                        if "front" in card and "back" in card:
                            # Ensure topic exists
                            if "topic" not in card:
                                card["topic"] = "General"
                            validated_cards.append(card)
                    
                    return validated_cards[:num_cards]
                except json.JSONDecodeError as e:
                    print(f"JSON parsing error for flashcards: {str(e)}")
                    
                    # Try a more aggressive cleanup
                    try:
                        # Remove any non-JSON syntax and hope for the best
                        json_str = json_str.replace("'", '"')
                        # Try to parse with ast first (more forgiving)
                        parsed = ast.literal_eval(json_str)
                        # Convert to proper JSON
                        cleaned_json = json.dumps(parsed)
                        flashcards = json.loads(cleaned_json)
                        return flashcards[:num_cards]
                    except Exception as e2:
                        print(f"Secondary parsing error: {str(e2)}")
            
            # If no JSON array was found, try to extract data in a different way
            # Look for patterns like "Front: ... Back: ..." in the text
            flashcards = []
            lines = response.split('\n')
            current_card = {}
            
            for line in lines:
                if line.strip().startswith("Front:") or line.strip().lower().startswith("question:"):
                    # Save previous card if it exists
                    if "front" in current_card and "back" in current_card:
                        flashcards.append(current_card)
                        current_card = {}
                    
                    # Start new card
                    front_text = line.split(":", 1)[1].strip()
                    current_card = {"front": front_text, "topic": "General"}
                    
                elif line.strip().startswith("Back:") or line.strip().lower().startswith("answer:"):
                    back_text = line.split(":", 1)[1].strip()
                    current_card["back"] = back_text
                    
            # Add the last card if there is one
            if "front" in current_card and "back" in current_card:
                flashcards.append(current_card)
            
            if flashcards:
                return flashcards[:num_cards]
                
            # If we still couldn't parse anything useful
            return [{"front": "Flashcard generation failed", 
                    "back": "Please try again with shorter or clearer content",
                    "topic": "Error"}]
        except Exception as e:
            print(f"Error parsing flashcards: {type(e).__name__}: {str(e)}")
            return [{"front": "Error generating flashcards", 
                    "back": f"Error: {str(e)}",
                    "topic": "Error"}]
    
    async def recommend_next_steps(
        self,
        user_data: Dict[str, Any],
        recent_activities: List[Dict[str, Any]],
        model: str = "llama2:7b"
    ) -> List[Dict[str, str]]:
        """Generate personalized recommendations for next study steps."""
        # Format the user data and recent activities as a prompt
        activities_str = json.dumps(recent_activities, indent=2)
        user_str = json.dumps(user_data, indent=2)
        
        prompt = f"""Based on this user's performance and recent study activities, recommend 1-3 next steps for their study journey.
The recommendations should be personalized, actionable, and based on their performance patterns.

User Data:
{user_str}

Recent Activities (newest first):
{activities_str}

Provide recommendations focusing on:
1. Weak topics that need more practice
2. Suggested study methods (quizzes, flashcards, summaries)
3. Specific content to review

Format your response as a JSON array:
[
  {{
    "title": "Practice More on [Topic]",
    "description": "Your detailed recommendation",
    "reason": "Why you're recommending this"
  }},
  // more recommendations...
]
"""
        
        response = await self.generate_completion(
            prompt=prompt,
            model=model,
            temperature=0.7,
            max_tokens=1000
        )
        
        # Extract JSON array from the response
        try:
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                # Clean up JSON string
                json_str = re.sub(r'//.*', '', json_str)  # Remove // comments
                json_str = re.sub(r',(\s*[\]}])', r'\1', json_str)  # Remove trailing commas
                
                try:
                    recommendations = json.loads(json_str)
                    return recommendations[:3]  # Limit to 3 recommendations max
                except json.JSONDecodeError:
                    # Try a more aggressive cleanup
                    try:
                        json_str = json_str.replace("'", '"')
                        parsed = ast.literal_eval(json_str)
                        cleaned_json = json.dumps(parsed)
                        recommendations = json.loads(cleaned_json)
                        return recommendations[:3]
                    except:
                        return []
            
            return []
        except:
            # If JSON parsing fails
            return []
