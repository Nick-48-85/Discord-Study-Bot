"""
Test the enhanced summarization functionality.
"""

import asyncio
import os
from study_coach.services.ollama import OllamaService, PromptType
from study_coach.services.summarization import EnhancedSummarizationService

# Sample text for testing hallucination prevention - a mix of AI topics and EV content
MIXED_CONTENT = """
First-order logic (FOL) extends propositional logic by including variables, 
functions, and predicates. In FOL, we have the following components:

1. Constants: Represent specific objects in the domain (e.g., John, 3)
2. Variables: Represent objects without specifying which one (e.g., x, y)
3. Predicates: Represent relations or properties (e.g., Father(x,y), Greater(x,y))
4. Functions: Map objects to objects (e.g., Mother(x), SquareRoot(x))
5. Quantifiers: ∀ (universal) and ∃ (existential)

Modus Ponens is a fundamental rule of inference in propositional and first-order logic.
It states that if we know P → Q (if P then Q) and we know P is true, then we can infer Q.

In knowledge representation, we use the notation KB ⊨ f to indicate that a formula f
is entailed by the knowledge base KB, meaning that f is true in all worlds where KB is true.

Electric vehicles (EVs) are transforming transportation by using electricity stored
in rechargeable batteries instead of fossil fuels. The United States offers a federal tax 
credit of up to $7,500 for the purchase of an EV. Modern lithium-ion batteries have seen 
cost decreases of over 70% in the past decade, while energy density has improved significantly.
The growing charging infrastructure network includes Level 1 (120V), Level 2 (240V), and 
DC fast charging options.

A Markov Decision Process (MDP) is a mathematical framework for modeling decision-making
in situations where outcomes are partly random and partly under the control of a decision-maker.
An MDP consists of:
- States: S
- Actions: A
- Transition probabilities: P(s'|s,a)
- Rewards: R(s,a,s')
- Discount factor: γ

Evolutionary algorithms are optimization techniques inspired by natural evolution.
They maintain a population of candidate solutions and apply operations like:
- Selection: Choosing the fittest individuals
- Crossover: Combining parts of different solutions
- Mutation: Randomly altering parts of solutions
"""

# Pure AI content without EV contamination
AI_CONTENT = """
First-order logic (FOL) extends propositional logic by including variables, 
functions, and predicates. In FOL, we have the following components:

1. Constants: Represent specific objects in the domain (e.g., John, 3)
2. Variables: Represent objects without specifying which one (e.g., x, y)
3. Predicates: Represent relations or properties (e.g., Father(x,y), Greater(x,y))
4. Functions: Map objects to objects (e.g., Mother(x), SquareRoot(x))
5. Quantifiers: ∀ (universal) and ∃ (existential)

Modus Ponens is a fundamental rule of inference in propositional and first-order logic.
It states that if we know P → Q (if P then Q) and we know P is true, then we can infer Q.

In knowledge representation, we use the notation KB ⊨ f to indicate that a formula f
is entailed by the knowledge base KB, meaning that f is true in all worlds where KB is true.

A Markov Decision Process (MDP) is a mathematical framework for modeling decision-making
in situations where outcomes are partly random and partly under the control of a decision-maker.
An MDP consists of:
- States: S
- Actions: A
- Transition probabilities: P(s'|s,a)
- Rewards: R(s,a,s')
- Discount factor: γ

Evolutionary algorithms are optimization techniques inspired by natural evolution.
They maintain a population of candidate solutions and apply operations like:
- Selection: Choosing the fittest individuals
- Crossover: Combining parts of different solutions
- Mutation: Randomly altering parts of solutions
"""

async def test_summarization():
    """Test the enhanced summarization service with validation."""
    print("Initializing services...")
    
    # Initialize services
    ollama_service = OllamaService(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    )
    summarization_service = EnhancedSummarizationService(ollama_service)
    
    # Test 1: Standard AI content summarization with validation
    print("\nTest 1: Summarizing AI content with validation...")
    summary_result = await summarization_service.summarize_document(
        document_text=AI_CONTENT,
        max_points=5,
        validation_enabled=True
    )
    
    print("AI Content Summary:")
    for i, point in enumerate(summary_result["summary"]):
        print(f"  {i+1}. {point}")
    
    # Test 2: Mixed content without validation (should potentially include EV content)
    print("\nTest 2: Summarizing mixed content WITHOUT validation...")
    mixed_result_no_validation = await summarization_service.summarize_document(
        document_text=MIXED_CONTENT,
        max_points=5,
        validation_enabled=False
    )
    
    print("Mixed Content Summary WITHOUT Validation:")
    for i, point in enumerate(mixed_result_no_validation["summary"]):
        print(f"  {i+1}. {point}")
    
    # Test 3: Mixed content with validation (should filter out EV content)
    print("\nTest 3: Summarizing mixed content WITH validation...")
    mixed_result_with_validation = await summarization_service.summarize_document(
        document_text=MIXED_CONTENT,
        max_points=5,
        validation_enabled=True
    )
    
    print("Mixed Content Summary WITH Validation:")
    for i, point in enumerate(mixed_result_with_validation["summary"]):
        print(f"  {i+1}. {point}")
    
    # Check for EV-related terms in summaries
    ev_terms = ["electric", "vehicles", "EV", "battery", "batteries", "charging", "lithium"]
    
    def contains_ev_terms(text):
        return any(term.lower() in text.lower() for term in ev_terms)
    
    no_validation_has_ev = any(contains_ev_terms(point) for point in mixed_result_no_validation["summary"])
    with_validation_has_ev = any(contains_ev_terms(point) for point in mixed_result_with_validation["summary"])
    
    print("\nResults analysis:")
    print(f"  Without validation contains EV terms: {no_validation_has_ev}")
    print(f"  With validation contains EV terms: {with_validation_has_ev}")
    
    if not with_validation_has_ev and no_validation_has_ev:
        print("✅ SUCCESS: Validation successfully filtered out irrelevant EV content!")
    elif not no_validation_has_ev:
        print("⚠️ INCONCLUSIVE: Neither summary contained EV terms")
    else:
        print("❌ FAILED: Validation did not filter out irrelevant EV content")

if __name__ == "__main__":
    asyncio.run(test_summarization())
