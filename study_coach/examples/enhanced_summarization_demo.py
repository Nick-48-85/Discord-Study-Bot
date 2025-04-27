"""
Example demonstrating the enhanced summarization service with hallucination prevention.
"""

import os
import asyncio
from pprint import pprint

from study_coach.services import OllamaService, EnhancedSummarizationService


async def main():
    """Demonstrate the enhanced summarization service."""
    # Sample AI course content
    ai_course_content = """
    First-order logic (FOL) extends propositional logic by including variables, 
    functions, and predicates. In FOL, we have the following components:
    
    1. Constants: Represent specific objects in the domain (e.g., John, 3)
    2. Variables: Represent objects without specifying which one (e.g., x, y)
    3. Predicates: Represent relations or properties (e.g., Father(x,y), Greater(x,y))
    4. Functions: Map objects to objects (e.g., Mother(x), SquareRoot(x))
    5. Quantifiers: ∀ (universal) and ∃ (existential)
    
    Modus Ponens is a fundamental rule of inference in propositional and first-order logic.
    It states that if we know P → Q (if P then Q) and we know P is true, then we can infer Q.
    For example, if we know "If it's raining, the ground is wet" and we observe "It's raining",
    then we can conclude "The ground is wet".
    
    In knowledge representation, we use the notation KB ⊨ f to indicate that a formula f
    is entailed by the knowledge base KB, meaning that f is true in all worlds where KB is true.
    
    Unification is the process of finding substitutions that make different logical expressions identical.
    For example, unifying P(x,B) and P(A,y) would yield the substitution {x/A, y/B}.
    
    A Markov Decision Process (MDP) is a mathematical framework for modeling decision-making
    in situations where outcomes are partly random and partly under the control of a decision-maker.
    An MDP consists of:
    - States: S
    - Actions: A
    - Transition probabilities: P(s'|s,a)
    - Rewards: R(s,a,s')
    - Discount factor: γ
    
    The goal in an MDP is to find a policy π that maximizes the expected discounted reward.
    
    Evolutionary algorithms are optimization techniques inspired by natural evolution.
    They maintain a population of candidate solutions and apply operations like:
    - Selection: Choosing the fittest individuals
    - Crossover: Combining parts of different solutions
    - Mutation: Randomly altering parts of solutions
    
    These algorithms are particularly useful for numerical optimization problems
    where the search space is large and complex.
    
    Model-based reinforcement learning methods build a model of the environment,
    which allows the agent to simulate and plan future actions without directly
    interacting with the environment. This can be more sample-efficient but requires
    accurate modeling of the environment dynamics.
    """
    
    print("Initializing services...")
    ollama_service = OllamaService(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    )
    
    summarization_service = EnhancedSummarizationService(ollama_service)
    
    print("\n1. Standard summarization with validation:")
    summary_result = await summarization_service.summarize_document(
        document_text=ai_course_content,
        max_points=5,
        validation_enabled=True
    )
    
    print("\nSummary points:")
    for i, point in enumerate(summary_result["summary"]):
        print(f"  {i+1}. {point}")
    
    print("\nExtracted document topics:")
    topics = summary_result.get("topics", {})
    print("  Subject Areas:", ", ".join(topics.get("subject_areas", [])))
    print("  Key Topics:", ", ".join(topics.get("key_topics", [])))
    
    if "validation" in summary_result:
        print(f"\nValidation results:")
        validation = summary_result["validation"]
        print(f"  Valid points: {validation.get('total_points', 0) - validation.get('invalid_points_count', 0)}/{validation.get('total_points', 0)}")
    
    # Test with problematic content mixing AI terms with unrelated topics
    mixed_content = ai_course_content + """
    
    Electric vehicles (EVs) are transforming transportation by using electricity stored
    in rechargeable batteries instead of fossil fuels. The United States offers a federal tax 
    credit of up to $7,500 for the purchase of an EV. Modern lithium-ion batteries have seen 
    cost decreases of over 70% in the past decade, while energy density has improved significantly.
    The growing charging infrastructure network includes Level 1 (120V), Level 2 (240V), and 
    DC fast charging options.
    """
    
    print("\n\n2. Handling of mixed content (with AI terms and EV information):")
    mixed_result = await summarization_service.summarize_document(
        document_text=mixed_content,
        max_points=5,
        validation_enabled=True
    )
    
    print("\nSummary points (should focus on AI content):")
    for i, point in enumerate(mixed_result["summary"]):
        print(f"  {i+1}. {point}")


if __name__ == "__main__":
    asyncio.run(main())
