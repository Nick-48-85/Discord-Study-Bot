"""
Main bot module for Discord Adaptive Study Coach.
"""

import os
import uuid
import discord
import datetime
import asyncio
import hashlib
from typing import Dict, List, Any, Optional, Union, Tuple
from discord import app_commands
from discord.ext import commands

from owlmind.bot import BotEngine, BotMessage
from owlmind.discord import DiscordBot

# Use absolute imports instead of relative imports
from .services.database import DatabaseService
from .services.ollama import OllamaService, PromptType
# Using the enhanced service directly now
from .services.summarization import EnhancedSummarizationService
from .services.qa_dataset import QADatasetService
from .utils.document import DocumentProcessor
from .utils.analytics import AnalyticsVisualizer
from .models.models import (
    UserProfile, StudyMaterial, QuizQuestion, 
    QuizAttempt, StudySession, DifficultyLevel
)
from .models.enhanced_models import (
    EnhancedQuizQuestion, QuestionFeedback, QAChangelog, FeedbackRating
)

# Import the command modules with relative imports
from .commands.study_commands import StudyCommands
from .commands.quiz_commands import QuizCommands
from .commands.analytics_commands import AnalyticsCommands


class StudyCoachBotEngine(BotEngine):
    """Study Coach bot engine built on OwlMind framework."""
    def __init__(self, db_service: DatabaseService, ollama_service: OllamaService, 
                 ollama_enhanced: OllamaService = None, 
                 summarization_service: EnhancedSummarizationService = None,
                 qa_service: QADatasetService = None):
        """Initialize the study coach bot engine."""
        super().__init__(id='study_coach')  # Passing the required id parameter
        self.db = db_service
        self.ollama = ollama_service
        self.ollama_enhanced = ollama_enhanced
        self.summarization_service = summarization_service
        self.qa_service = qa_service
        self.doc_processor = DocumentProcessor()
        self.active_sessions = {}  # {user_id: session_data}
    
    async def process(self, message: BotMessage) -> str:
        """Process incoming messages."""
        # This is called for regular messages, but most functionality
        # will be handled through slash commands
        return "I'm your Study Coach! Use slash commands like /help to interact with me."


class StudyCoachBot(commands.Bot):
    """Discord Adaptive Study Coach bot."""
    def __init__(
        self, 
        token: str,
        mongo_uri: Optional[str] = None,
        ollama_url: Optional[str] = "http://localhost:11434"    ):
        """Initialize the study coach bot."""
        # Create intents with privileged intents now enabled in Discord Developer Portal
        intents = discord.Intents.default()
        intents.message_content = True  # Privileged intent now enabled
        intents.members = True  # Privileged intent now enabled
        super().__init__(command_prefix='!', intents=intents)
        self.token = token
        self.db = DatabaseService(mongo_uri)
          # Initialize the Ollama service
        self.ollama = OllamaService(ollama_url)
        self.ollama_enhanced = self.ollama  # For backward compatibility
        self.summarization_service = EnhancedSummarizationService(self.ollama_enhanced)
        self.qa_service = QADatasetService(self.db, self.ollama_enhanced)
        
        self.bot_engine = StudyCoachBotEngine(
            self.db, 
            self.ollama,
            self.ollama_enhanced,
            self.summarization_service,
            self.qa_service
        )
        self.active_quizzes = {}  # {message_id: quiz_data}
        self.active_flashcards = {}  # {message_id: flashcard_data}
    
    async def setup_hook(self) -> None:
        """Set up the bot and register commands."""
        await self.db.create_indexes()
        await self.add_cog(UserCommands(self))
        await self.add_cog(StudyCommands(self))
        await self.add_cog(QuizCommands(self))
        await self.add_cog(AnalyticsCommands(self))
        await self.tree.sync()
    
    async def on_ready(self):
        """Called when the bot is ready."""
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")
        
        # Set custom status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name="/help | Your Study Assistant"
            )
        )
    
    def run(self):
        """Run the bot with the provided token."""
        super().run(self.token, reconnect=True)


class UserCommands(commands.Cog):
    """Commands for user management."""
    
    def __init__(self, bot: StudyCoachBot):
        """Initialize user commands."""
        self.bot = bot
    
    @app_commands.command(
        name="register",
        description="Register with the Study Coach bot"
    )
    async def register(self, interaction: discord.Interaction):
        """Register a new user with the bot."""
        # Check if user already exists
        user = await self.bot.db.get_user_by_discord_id(str(interaction.user.id))
        
        if user:
            await interaction.response.send_message(
                "You're already registered! Use /help to see available commands.",
                ephemeral=True
            )
            return
        
        # Create new user profile
        new_user = UserProfile(
            id=str(uuid.uuid4()),
            discord_id=str(interaction.user.id),
            username=interaction.user.name,
            difficulty_preference=DifficultyLevel.MEDIUM
        )
        
        await self.bot.db.create_user(new_user)
        
        # Send welcome message
        embed = discord.Embed(
            title="Welcome to Study Coach!",
            description=(
                "Thanks for registering! Here's what you can do:\n\n"
                "📚 Upload study materials with `/upload`\n"
                "📝 Generate quizzes with `/quiz`\n"
                "🗂️ Create flashcards with `/flashcards`\n"
                "📊 Track your progress with `/progress`\n\n"
                "Use `/help` to see all available commands."
            ),
            color=discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed)
        
        # Send a welcome DM
        try:
            dm_embed = discord.Embed(
                title="Study Coach - Personal Assistant",
                description=(
                    "Hi there! I'm your personal Study Coach. I'll help you "
                    "study effectively by creating quizzes, flashcards, and "
                    "summaries based on your materials.\n\n"
                    "Get started by uploading study content with `/upload` in any channel."
                ),
                color=discord.Color.blue()
            )
            
            await interaction.user.send(embed=dm_embed)
        except:
            # User might have DMs disabled
            pass
    
    @app_commands.command(
        name="profile",
        description="View your study profile and statistics"
    )
    async def profile(self, interaction: discord.Interaction):
        """View user profile and study statistics."""
        # Get user profile
        user = await self.bot.db.get_user_by_discord_id(str(interaction.user.id))
        
        if not user:
            await interaction.response.send_message(
                "You need to register first! Use `/register` to get started.",
                ephemeral=True
            )
            return
        
        # Get user stats
        accuracy = f"{user.correct_answers / user.total_questions_answered * 100:.1f}%" if user.total_questions_answered > 0 else "N/A"
        
        # Get recent sessions
        recent_sessions = await self.bot.db.get_sessions_by_user(user.id, limit=5)
        
        # Create embed
        embed = discord.Embed(
            title=f"Study Profile: {interaction.user.name}",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Total Sessions", value=str(user.session_count), inline=True)
        embed.add_field(name="Questions Answered", value=str(user.total_questions_answered), inline=True)
        embed.add_field(name="Accuracy", value=accuracy, inline=True)
        embed.add_field(name="Difficulty Preference", value=user.difficulty_preference.value.capitalize(), inline=True)
        
        if user.topics_of_interest:
            embed.add_field(name="Topics of Interest", value=", ".join(user.topics_of_interest), inline=False)
        
        if recent_sessions:
            recent_activity = "\n".join([
                f"• {s.session_type.capitalize()} on {s.start_time.strftime('%Y-%m-%d')}" +
                (f" - Score: {s.score:.1f}%" if s.score is not None else "")
                for s in recent_sessions
            ])
            embed.add_field(name="Recent Activity", value=recent_activity, inline=False)
        
        # Add recommendations if any
        if user.session_count > 0:
            # Get user data in a format suitable for the recommender
            user_data = {
                "accuracy": float(accuracy.strip('%')) if accuracy != "N/A" else 0,
                "session_count": user.session_count,
                "topics_of_interest": user.topics_of_interest,
                "difficulty_preference": user.difficulty_preference.value
            }
            
            # Format recent sessions for the recommender
            recent_activities = [
                {
                    "type": s.session_type,
                    "date": s.start_time.isoformat(),
                    "score": s.score if s.score is not None else None,
                    "total_questions": s.total_questions,
                    "correct_answers": s.correct_answers,
                    "topics": s.topics,
                    "difficulty": s.difficulty.value if s.difficulty else None
                }
                for s in recent_sessions
            ]
            
            # Get recommendations
            if recent_activities:
                recommendations = await self.bot.ollama.recommend_next_steps(user_data, recent_activities)
                
                if recommendations:
                    rec_text = "\n".join([f"• **{r['title']}**: {r['description']}" for r in recommendations])
                    embed.add_field(name="Personalized Recommendations", value=rec_text, inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(
        name="setdifficulty",
        description="Set your preferred difficulty level for quizzes"
    )
    @app_commands.choices(difficulty=[
        app_commands.Choice(name="Easy", value="easy"),
        app_commands.Choice(name="Medium", value="medium"),
        app_commands.Choice(name="Hard", value="hard"),
    ])
    async def set_difficulty(self, interaction: discord.Interaction, difficulty: app_commands.Choice[str]):
        """Set the user's preferred difficulty level."""
        # Get user profile
        user = await self.bot.db.get_user_by_discord_id(str(interaction.user.id))
        
        if not user:
            await interaction.response.send_message(
                "You need to register first! Use `/register` to get started.",
                ephemeral=True
            )
            return
        
        # Update difficulty preference
        user.difficulty_preference = DifficultyLevel(difficulty.value)
        await self.bot.db.update_user(user)
        
        await interaction.response.send_message(
            f"Your difficulty preference has been updated to **{difficulty.name}**!",
            ephemeral=True
        )
    
    @app_commands.command(
        name="help",
        description="Show help information about the study coach bot"
    )
    async def help(self, interaction: discord.Interaction):
        """Show help information."""
        embed = discord.Embed(
            title="Study Coach Help",
            description="Here are all the commands you can use:",
            color=discord.Color.blue()
        )
        
        # User commands
        user_cmds = (
            "`/register` - Register with the Study Coach bot\n"
            "`/profile` - View your study profile and statistics\n"
            "`/setdifficulty` - Set your preferred difficulty level"
        )
        embed.add_field(name="User Commands", value=user_cmds, inline=False)
        
        # Study material commands
        study_cmds = (
            "`/upload` - Upload study material (PDF, text, URL)\n"
            "`/materials` - List your study materials\n"
            "`/summarize` - Generate a summary of a study material"
        )
        embed.add_field(name="Study Material Commands", value=study_cmds, inline=False)
        
        # Quiz commands
        quiz_cmds = (
            "`/quiz` - Create a new quiz from your materials\n"
            "`/flashcards` - Create flashcards from your materials"
        )
        embed.add_field(name="Quiz Commands", value=quiz_cmds, inline=False)
        
        # Analytics commands
        analytics_cmds = (
            "`/progress` - View your progress statistics and charts\n"
            "`/history` - View your session history for a specific date"
        )
        embed.add_field(name="Analytics Commands", value=analytics_cmds, inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
