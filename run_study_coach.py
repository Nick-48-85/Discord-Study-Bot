"""
Modified entry point for the Discord Adaptive Study Coach bot.
This version includes explicit sys.path manipulation to ensure
the correct modules are found.
"""

print("*** Starting Discord Adaptive Study Coach script ***")

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Now import from study_coach
from study_coach.bot import StudyCoachBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('study_coach')

# Load environment variables
load_dotenv()

# Get configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')

if not DISCORD_TOKEN:
    logger.error("No Discord token found. Set the DISCORD_TOKEN environment variable.")
    sys.exit(1)

def main():
    """Run the Discord Adaptive Study Coach bot."""
    logger.info("Starting Discord Adaptive Study Coach")
    
    # Initialize the bot
    bot = StudyCoachBot(
        token=DISCORD_TOKEN,
        mongo_uri=MONGO_URI,
        ollama_url=OLLAMA_URL
    )
    
    # Run the bot
    bot.run()

if __name__ == "__main__":
    main()
