# Study Coach Services

This directory contains the core service modules for the Study Coach application.

## Service Modules

- **database.py**: MongoDB integration using Motor for asynchronous database operations
- **ollama_enhanced.py**: Primary Ollama API service with temperature control and structured responses
- **summarization.py**: Enhanced text summarization with topic detection and validation
- **qa_dataset.py**: Question-answer dataset creation and management
- **prompts.py**: Prompt templates for different AI tasks

## Recent Changes

### April 2025 - Service Consolidation

We've consolidated the Ollama service implementation by replacing the original `OllamaService` with the enhanced `OllamaEnhancedService`. The enhanced service provides:

1. **Temperature Controls**: Automatic temperature selection based on task type:
   - `0.3` for factual tasks (summarization, Q&A)
   - `0.7` for creative tasks (flashcards, recommendations)
   - `0.5` for default/mixed tasks
   
2. **Structured JSON Responses**: Better parsing and handling of structured API responses
   - Automatic cleaning of malformed JSON
   - Schema-based prompting
   - Fallback strategies for parsing errors
   
3. **Improved Error Handling**: More robust error handling for API calls

### Backward Compatibility

For backward compatibility, we maintain:
- `from study_coach.services import OllamaService` will import the enhanced service
- A compatibility layer in `ollama_compatibility.py`

### Migration Strategy

1. See `migration_plan.md` for the full migration strategy
2. See `migration_status.md` for current migration status
3. Run `examples/test_migration.py` to verify the migration works correctly

## Best Practices

When working with these services:

1. Import directly from the enhanced service:
   ```python
   from study_coach.services.ollama_enhanced import OllamaEnhancedService, PromptType
   ```

2. Use the appropriate prompt type for temperature control:
   ```python
   # For factual/exact responses
   response = await ollama.generate_structured_completion(
       prompt="Summarize this text",
       prompt_type=PromptType.FACTUAL
   )
   
   # For creative tasks
   response = await ollama.generate_completion(
       prompt="Write a story",
       prompt_type=PromptType.CREATIVE
   )
   ```

3. Use structured responses where possible:
   ```python
   schema = {
       "summary": ["string"],
       "keywords": ["string"],
       "difficulty": "string" 
   }
   
   response = await ollama.generate_structured_completion(
       prompt=prompt,
       schema=schema,
       prompt_type=PromptType.FACTUAL
   )
   ```
