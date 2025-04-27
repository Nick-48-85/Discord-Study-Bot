"""
Simple script to start the Discord Adaptive Study Coach bot.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Use DEBUG level for more detailed logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('study_coach')
logger.setLevel(logging.DEBUG)

# Add current directory to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Load environment variables
load_dotenv()

# Log some diagnostic information
logger.debug("Python executable: %s", sys.executable)
logger.debug("Python path: %s", sys.path)

# Get configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')

logger.debug("Discord Token: %s", DISCORD_TOKEN[:5] + '...' if DISCORD_TOKEN else None)
logger.debug("MongoDB URI: %s", MONGO_URI)
logger.debug("Ollama URL: %s", OLLAMA_URL)

try:
    # Import the bot
    logger.debug("Importing StudyCoachBot...")
    from study_coach.bot import StudyCoachBot
    logger.debug("Successfully imported StudyCoachBot")
    
    # Initialize the bot
    logger.debug("Initializing StudyCoachBot...")
    bot = StudyCoachBot(
        token=DISCORD_TOKEN,
        mongo_uri=MONGO_URI,
        ollama_url=OLLAMA_URL
    )
    logger.debug("Successfully initialized StudyCoachBot")
    
    # Run the bot
    logger.info("Starting Discord Adaptive Study Coach")
    bot.run()
except Exception as e:
    logger.exception("Error starting the Discord Adaptive Study Coach bot: %s", e)
