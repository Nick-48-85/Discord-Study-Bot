"""
Enhanced document summarization service with hallucination prevention.
"""

import json
import asyncio
from typing import List, Dict, Any, Optional, Union, Tuple
import re

from .ollama import OllamaService, PromptType
from .prompts import SummarizationPrompts, DetectionPrompts


class EnhancedSummarizationService:
    """Service for high-quality document summarization with validation."""
    def __init__(self, ollama_service: OllamaService):
        """
        Initialize the summarization service.
        
        Args:
            ollama_service: The Ollama service for LLM requests
        """
        self.ollama = ollama_service
        self.min_similarity_threshold = 0.5  # Minimum similarity for valid summaries
    
    async def summarize_document(
        self,
        document_text: str,
        max_points: int = 10,
        model: str = "llama2:7b",
        validation_enabled: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a validated summary of document content.
        
        Args:
            document_text: The document text to summarize
            max_points: Maximum number of bullet points to generate
            model: The LLM model to use
            validation_enabled: Whether to validate summary points
            
        Returns:
            Dictionary with summary points and validation info
        """
        if len(document_text) < 100:
            return {
                "success": False,
                "error": "Document too short to summarize meaningfully",
                "summary": ["Document contains insufficient content for summarization."]
            }
        
        # Truncate long documents
        if len(document_text) > 12000:
            document_text = document_text[:12000] + "..."
        
        # Step 1: Extract document topics for context
        topics = await self._extract_document_topics(document_text, model)
        
        # Step 2: Generate initial summary with topic guidance
        summary_points = await self._generate_summary_points(
            document_text, max_points, topics.get("key_topics", []), model
        )
        
        result = {
            "success": True,
            "summary": summary_points,
            "topics": topics
        }
        
        # Step 3: Validate summary if enabled
        if validation_enabled and summary_points:
            validation = await self._validate_summary(summary_points, document_text, model)
            result["validation"] = validation
            
            # Step 4: Regenerate problematic points if necessary
            if validation.get("invalid_points_count", 0) > 0:
                # Filter out invalid points
                valid_points = [p["point"] for p in validation.get("point_analysis", []) 
                               if p.get("supported", False)]
                
                # If we lost more than 30% of our points, regenerate
                if len(valid_points) < 0.7 * len(summary_points):
                    # Generate replacement summary with stricter constraints
                    replacement_summary = await self._generate_replacement_summary(
                        document_text, max_points, topics.get("key_topics", []), model
                    )
                    
                    if replacement_summary:
                        result["summary"] = replacement_summary
                        result["regenerated"] = True
                else:
                    # Just use the valid points
                    result["summary"] = valid_points
                    result["filtered"] = True
        
        return result
    
    async def _extract_document_topics(
        self, document_text: str, model: str
    ) -> Dict[str, List[str]]:
        """
        Extract key topics from document to guide summarization.
        
        Args:
            document_text: The document text
            model: Model to use
            
        Returns:
            Dictionary with subject areas and key topics
        """
        # Create topic extraction prompt
        prompt = SummarizationPrompts.get_topic_extraction_prompt(document_text)
        
        try:
            # Use factual prompt type (temperature=0.3) for accurate extraction
            response = await self.ollama.generate_structured_completion(
                prompt=prompt,
                prompt_type=PromptType.FACTUAL,
                model=model,
                max_tokens=500
            )
            
            # Extract subject areas and key topics
            subject_areas = response.get("subject_areas", [])
            key_topics = response.get("key_topics", [])
            
            # Ensure we have at least some topics
            if not key_topics and not subject_areas:
                # Default topics for academic documents if extraction failed
                return {
                    "subject_areas": ["Academic", "Education", "Study Material"],
                    "key_topics": ["Concepts", "Definitions", "Key Points"]
                }
            
            return {
                "subject_areas": subject_areas,
                "key_topics": key_topics
            }
            
        except Exception as e:
            print(f"Error extracting document topics: {type(e).__name__}: {str(e)}")
            # Return empty topics on failure
            return {
                "subject_areas": [],
                "key_topics": []
            }
    
    async def _generate_summary_points(
        self, 
        document_text: str, 
        max_points: int,
        topic_keywords: List[str],
        model: str
    ) -> List[str]:
        """
        Generate summary bullet points with topic guidance.
        
        Args:
            document_text: The document text
            max_points: Maximum number of points
            topic_keywords: Keywords to guide summarization
            model: Model to use
            
        Returns:
            List of summary bullet points
        """
        # Create enhanced prompt with topics for context
        prompt = SummarizationPrompts.get_document_summary_prompt(
            document_text, max_points, topic_keywords
        )
        
        try:
            # Use factual prompt type (temperature=0.3) for accurate summarization
            response = await self.ollama.generate_completion(
                prompt=prompt,
                model=model,
                temperature=0.3,
                top_p=0.95,
                max_tokens=1000
            )
            
            # Extract JSON array
            bullets = self._extract_json_array(response)
            
            # Clean and format bullets
            formatted_bullets = []
            for bullet in bullets[:max_points]:
                # Clean up bullet point format
                clean_bullet = bullet.strip()
                if clean_bullet.startswith('- '):
                    clean_bullet = clean_bullet[2:]
                if clean_bullet.startswith('• '):
                    clean_bullet = clean_bullet[2:]
                    
                # Truncate if too long
                if len(clean_bullet) > 100:
                    clean_bullet = clean_bullet[:97] + "..."
                
                formatted_bullets.append(clean_bullet)
            
            return formatted_bullets
            
        except Exception as e:
            print(f"Error generating summary: {type(e).__name__}: {str(e)}")
            return ["Error: Unable to generate summary due to processing error. Please try again."]
    
    async def _validate_summary(
        self, 
        summary_points: List[str], 
        document_text: str,
        model: str
    ) -> Dict[str, Any]:
        """
        Validate summary points against the original document.
        
        Args:
            summary_points: The bullet points to validate
            document_text: The original document
            model: Model to use
            
        Returns:
            Validation results
        """
        # Create validation prompt
        prompt = SummarizationPrompts.get_summary_validation_prompt(
            summary_points, document_text
        )
        
        try:
            # Use factual prompt type (temperature=0.3) for accurate validation
            response = await self.ollama.generate_structured_completion(
                prompt=prompt,
                prompt_type=PromptType.FACTUAL,
                model=model,
                max_tokens=1500
            )
            
            # Process validation results
            point_analysis = response.get("result", [])
            if not isinstance(point_analysis, list):
                point_analysis = []
            
            # Count invalid points
            invalid_points = [p for p in point_analysis if not p.get("supported", False)]
            
            return {
                "point_analysis": point_analysis,
                "invalid_points_count": len(invalid_points),
                "total_points": len(point_analysis)
            }
            
        except Exception as e:
            print(f"Error validating summary: {type(e).__name__}: {str(e)}")
            return {
                "error": str(e),
                "invalid_points_count": 0,
                "total_points": len(summary_points)
            }
    
    async def _generate_replacement_summary(
        self, 
        document_text: str, 
        max_points: int,
        topic_keywords: List[str],
        model: str
    ) -> List[str]:
        """
        Generate a replacement summary with stricter constraints.
        
        Args:
            document_text: The document text
            max_points: Maximum number of points
            topic_keywords: Keywords to guide summarization
            model: Model to use
            
        Returns:
            List of replacement summary bullet points
        """
        # Create a stronger prompt with explicit warning about previous hallucinations
        stronger_prompt = f"""CRITICAL INSTRUCTION: Previous attempts to summarize this document resulted in hallucinations.
You MUST be extremely careful to ONLY include information explicitly stated in the document.

{SummarizationPrompts.get_document_summary_prompt(document_text, max_points, topic_keywords)}

IMPORTANT REMINDER: Ensure EVERY bullet point directly references specific content from the document.
DO NOT include ANY information not explicitly found in the document text provided above.
"""
        
        try:
            # Use even lower temperature for stricter factuality
            response = await self.ollama.generate_completion(
                prompt=stronger_prompt,
                model=model,
                temperature=0.2,  # Lower temperature for maximum factuality
                top_p=0.9,  # Slightly lower top_p too
                max_tokens=1000
            )
            
            # Extract JSON array
            bullets = self._extract_json_array(response)
            
            # Clean and format bullets
            formatted_bullets = []
            for bullet in bullets[:max_points]:
                # Clean up bullet point format
                clean_bullet = bullet.strip()
                if clean_bullet.startswith('- '):
                    clean_bullet = clean_bullet[2:]
                if clean_bullet.startswith('• '):
                    clean_bullet = clean_bullet[2:]
                    
                # Truncate if too long
                if len(clean_bullet) > 100:
                    clean_bullet = clean_bullet[:97] + "..."
                
                formatted_bullets.append(clean_bullet)
            
            return formatted_bullets
            
        except Exception as e:
            print(f"Error generating replacement summary: {type(e).__name__}: {str(e)}")
            return []  # Return empty list to indicate failure
    
    def _extract_json_array(self, text: str) -> List[str]:
        """
        Extract a JSON array from text response.
        
        Args:
            text: Text potentially containing a JSON array
            
        Returns:
            Extracted array or empty list on failure
        """
        try:
            # Try to find JSON array in the response
            start_idx = text.find('[')
            end_idx = text.rfind(']') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = text[start_idx:end_idx]
                bullets = json.loads(json_str)
                return bullets
            
            # Fallback: try to parse bullets from text
            bullets = []
            for line in text.split('\n'):
                line = line.strip()
                if line.startswith('- ') or line.startswith('* ') or line.startswith('• '):
                    bullets.append(line[2:].strip())
            
            if bullets:
                return bullets
                
            # If nothing else works, just return the text split by newlines
            return [line.strip() for line in text.split('\n') if line.strip()]
            
        except json.JSONDecodeError:
            # Handle JSON parsing errors
            print("Error parsing JSON array from LLM response")
            
            # Try to extract bullet points from text format
            bullets = []
            for line in text.split('\n'):
                line = line.strip()
                if line.startswith('- ') or line.startswith('* ') or line.startswith('• '):
                    bullets.append(line[2:].strip())
            
            return bullets or ["Error: Unable to parse summary from model response."]
        except Exception as e:
            print(f"Unexpected error extracting JSON: {str(e)}")
            return ["Error: Unable to process the model's response."]
