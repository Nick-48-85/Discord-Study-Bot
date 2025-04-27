# Migration Plan: Replacing OllamaService with OllamaEnhancedService

## Overview

This document outlines the plan to consolidate our Ollama API integration by replacing the original `OllamaService` with the enhanced `OllamaEnhancedService` throughout the codebase.

## Justification

Having two separate services (`ollama.py` and `ollama_enhanced.py`) that perform similar functions leads to:
- Code duplication
- Maintenance overhead 
- Inconsistent functionality across the application
- Potential for bugs when features are updated in one service but not the other

The enhanced service provides additional capabilities like automatic temperature selection and structured JSON response handling, making it the preferred option.

## Steps to Migrate

1. **Make OllamaEnhancedService fully backward compatible**
   - Ensure it implements all methods from the original service
   - Maintain the same method signatures and behavior
   - Add any missing functionality

2. **Update imports and references**
   - Replace `from .ollama import OllamaService` with `from .ollama_enhanced import OllamaEnhancedService`
   - Update any type hints or function signatures that reference `OllamaService`
   - Fix any calls that might be relying on the specific behavior of the original service

3. **Test functionality**
   - Run existing tests to ensure everything still works
   - Test major features that interact with the Ollama API

4. **Remove the original service**
   - Delete `ollama.py` after confirming all references have been updated
   - Update documentation to reflect the change

## Files that need updating:

- `study_coach/services/__init__.py`
- `study_coach/commands/study_commands.py`
- `study_coach/commands/quiz_commands.py`
- `study_coach/bot.py`

## Potential Risks

- Breaking changes in method signatures or behavior
- Subtle differences in implementation that might affect behavior
- Integration points with other services that might be tightly coupled to the original service

## Mitigation

We will carefully review each usage of the original service and ensure the enhanced service maintains the same behavior for each method. We'll follow this with thorough testing to catch any issues.
