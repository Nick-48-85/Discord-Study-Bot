<img src="docs/images/owlmind-banner.png" width=800>

### [Understand](./README.md) | [Get Started](./README.md#getting-started) | [Contribute](./CONTRIBUTING.md)

# OwlMind Framework

The OwlMind Framework is being developed by The Generative Intelligence Lab at Florida Atlantic University to support education and experimentation with Hybrid Intelligence Systems. These solutions combine rule-based and generative AI (GenAI)-based inference to facilitate the implementation of local AI solutions, improving latency, optimizing costs, and reducing energy consumption and carbon emissions.

The framework is designed for both education and experimentation empowering students and researchers to rapidly build Hybrid AI-based Agentic Systems, achieving tangible results with minimal setup.

## Recent Updates

- **Service Unification (2025-04-27)**: Consolidated Ollama services by replacing `OllamaService` with the enhanced `OllamaEnhancedService` that provides improved temperature handling, structured JSON responses, and better error handling.
- **Enhanced Study Dataset (2025-04-20)**: Added support for automated QA generation with quality tracking based on user feedback.
- **Code Cleanup (2025-04-27)**: Removed unnecessary test files and improved project structure for better maintainability.
- **Documentation Improvements (2025-04-27)**: Enhanced README and configuration guides.

## Core Components

<img src="docs/images/owlmind-arch.png" width=800>

* **Bot Runner for Discord Bots:** Hosts and executes bots on platforms like Discord, providing users with an interactive conversational agent.
* **Agentic Core:** Enables deliberation and decision-making by allowing users to define and configure rule-based systems.
* **Configurable GenAI Pipelines:** Supports flexible and dynamic pipelines to integrate large-scale GenAI models into workflows.
* **Enhanced Study Dataset:** Automatically generates and improves question-answer pairs from study materials with user feedback tracking and adversarial examples.
* **Smart LLM Request Handler:** Intelligently sets temperature parameters based on task type and ensures consistent structured JSON responses.
* **Workflow Templates:** Provides pre-configured or customizable templates to streamline the Prompt Augmentation Process.
* **Artifacts:** Modular components that connect agents to external functionalities such as web APIs, databases, Retrieval-Augmented Generation (RAG) systems, and more.
* **Model Orchestrator:** Manages and integrates multiple GenAI models within pipelines, offering flexibility and simplicity for developers.

## Hybrid Intelligence Framework

The OwlMind architecture follows the principles of ``Hybrid Intelligence``, combining local rule-based inference with remote GenAI-assisted inference. This hybrid approach allows for multiple inference configurations:

* **GenAI generates the rules:**  The system leverages GenAI to create or refine rule-based logic, ensuring adaptability and efficiency.
* **Rules solve interactions; GenAI intervenes when needed:** if predefined rules are insufficient, the system escalates decision-making to the GenAI model.
* **Rules solve interactions and request GenAI to generate new rules:** instead of directly relying on GenAI for inference, the system asks it to expand its rule set dynamically.
* **Proactive rule generation for new contexts:** the system anticipates novel situations and queries GenAI for relevant rules before issues arise, ensuring continuous learning and adaptability.

## Agentic Core: Belief-Desire-Intention (BDI) Model

The ``Agentic Core`` adheres to the ``Belief-Desire-Intention (BDI) framework``, a cognitive architecture that enables goal-oriented agent behavior. The decision-making process is structured as follows:

* **Beliefs:** The agent's knowledge or perception of its environment, forming the foundation for evaluation and decision-making.
* **Desires:** The agent's objectives or goals, such as completing workflows, retrieving data, or responding to user queries.
* **Intentions:** The specific plans or strategies the agent commits to in order to achieve its desires, ensuring feasibility and optimization.
* **Plan Base:** A repository of predefined and dynamically generated plans, serving as actionable roadmaps to execute the agent's goals efficiently.
* **Capability Base:** Defines the agent's operational capabilities, specifying available actions and interactions; linked to existing Artifacts.

## Getting Started

Follow these steps to get started with OwlMind:

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/genilab-fau/owlmind.git
cd owlmind

# Set up a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

For more detailed installation instructions, see [INSTALLING.md](./INSTALLING.md).

### 2. Configuration

1. Create a Discord bot and get your token ([Discord Bot Setup Guide](./docs/discord.md))
2. Configure your environment settings:
   ```
   # Create a .env file with your Discord token and model settings
   DISCORD_TOKEN=your_discord_token_here
   SERVER_MODEL=llama3.2
   SERVER_TYPE=ollama
   SERVER_URL=http://localhost:11434
   ```
3. Set up a model provider ([Configuration Guide](./CONFIG.md))

### 3. Running the Bot

```bash
# Run a simple bot with rule-based responses
python -m owlmind.simple

# For the Study Coach bot
python run_study_coach.py
```

### 4. Advanced Configuration

* [Configure GenAI Pipelines](./CONFIG.md) to extend the Bot's conversation capabilities
* Create custom prompt templates in the `services/prompts.py` file
* Add additional artifacts in the GenAI pipelines for enhanced functionality

# Discord Adaptive Study Coach

An AI‑powered study bot for Discord, built on the OwlMind framework and connected to local AI models via an Ollama server. The bot helps students ingest study materials, generate quizzes, track performance, and receive personalized next‑step recommendations—all within Discord.

### Setting Up the Study Coach

1. Make sure you have [Ollama](https://ollama.ai/) installed and running
2. Install MongoDB (required for storing user data and analytics)
   ```bash
   # On Windows with Chocolatey
   choco install mongodb

   # On macOS with Homebrew
   brew tap mongodb/brew
   brew install mongodb-community
   ```
3. Start the bot
   ```bash
   python run_study_coach.py
   ```

### Available Commands

The study coach bot supports the following Discord slash commands:

- `/upload` - Upload study materials (PDF, text, or URL)
- `/quiz` - Generate a quiz based on uploaded materials
- `/summarize` - Create a summary of study materials
- `/progress` - View your study analytics and progress
- `/history` - Check your past study sessions
- `/help` - Get a list of available commands

## Solution Overview

This Discord Study Bot provides the following core functionalities:

1. **Personalized Quiz Generation**  
   Automatically generate multiple‑choice or short‑answer quizzes based on user‑provided documents or topics.

2. **Dynamic Content Summarization**  
   Summarize long texts (PDFs, lecture notes, articles) into bite‑sized study cards or bullet lists.

3. **Performance Tracking & Analytics**  
   Track user scores over time, identify weak areas, and visualize progress charts directly in Discord.

4. **Adaptive Learning Path Recommendations**  
   Suggest next best learning activities (e.g., drill more on weak topics, revisit summaries) based on past performance.

5. **Flashcard Drill Mode**  
   Turn key concepts into flashcards and quiz the user until mastery thresholds are met.

### How It Works

1. **User Registration & Context Setup**  
   - Student "joins" the bot on Discord and links their profile via OAuth.  
2. **Content Intake & Preprocessing**  
   - User uploads a document or specifies a topic; bot sends it to Ollama for embedding, summarization, or question generation.  
3. **AI‑Powered Task Execution**  
   - Ollama models generate quizzes, summaries, or flashcards; bot formats and posts them as interactive Discord messages.  
4. **Interaction & Feedback Loop**  
   - Student completes the quiz or reviews the summary; bot logs responses, timestamps, and correctness.  
5. **Adaptive Adjustment**  
   - Bot recalibrates difficulty and suggests new content based on tracked performance metrics.  
6. **Analytics & Reporting**  
   - On `/progress`, bot compiles charts and stats (accuracy by topic, time spent, mastery levels) and delivers them in Discord.

## Project Structure

The project is organized as follows:

```
owlmind/               # Core framework
├── __init__.py        # Package initialization
├── agent.py           # Agent implementation
├── bot.py             # Base bot functionality
├── context.py         # Context management
├── discord.py         # Discord integration
├── pipeline.py        # GenAI pipeline implementation
└── simple.py          # Simple bot engine

study_coach/           # Study Coach implementation
├── commands/          # Discord slash commands
├── examples/          # Example implementations
├── models/            # Data models
├── services/          # Core services (DB, Ollama, etc.)
└── utils/             # Utility functions

rules/                 # Rule definitions for bots
├── bot-rules-1.csv    # Basic conversation rules
├── bot-rules-2.csv    # Requirement analysis rules
└── bot-rules-3.csv    # GenAI pipeline rules

docs/                  # Documentation
tests/                 # Unit and integration tests
```

## Contributing

We welcome contributions to the OwlMind project! Please see our [Contributing Guidelines](./CONTRIBUTING.md) for more information on how to get involved.

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.
