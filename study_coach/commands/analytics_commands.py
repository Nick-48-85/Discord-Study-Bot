"""
Commands for analytics functionality in the Discord Adaptive Study Coach.
"""

import discord
import datetime
import io
from discord import app_commands
from discord.ext import commands
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime, timedelta

from ..utils.analytics import AnalyticsVisualizer
from ..models.models import DifficultyLevel


class AnalyticsCommands(commands.Cog):
    """Commands for analytics and progress tracking."""
    
    def __init__(self, bot):
        """Initialize analytics commands."""
        self.bot = bot
        self.db = bot.db
        self.visualizer = AnalyticsVisualizer()
    
    @app_commands.command(
        name="progress",
        description="View your study progress analytics and charts"
    )
    async def progress(self, interaction: discord.Interaction):
        """Show progress analytics and charts."""
        # Check if user is registered
        user = await self.db.get_user_by_discord_id(str(interaction.user.id))
        if not user:
            await interaction.response.send_message(
                "You need to register first! Use `/register` to get started.",
                ephemeral=True
            )
            return
        
        # Defer response since generating analytics might take time
        await interaction.response.defer(thinking=True)
        
        try:
            # Get recent sessions
            sessions = await self.db.get_sessions_by_user(user.id, limit=50)
            
            if not sessions:
                await interaction.followup.send(
                    "You haven't completed any study sessions yet. "
                    "Use `/quiz` or `/flashcards` to start studying!",
                    ephemeral=True
                )
                return
            
            # Calculate overall accuracy
            total_correct = sum(s.correct_answers for s in sessions if s.correct_answers is not None)
            total_questions = sum(s.total_questions for s in sessions if s.total_questions is not None)
            accuracy = (total_correct / total_questions * 100) if total_questions > 0 else 0
            
            # Calculate topic scores
            topic_scores: Dict[str, Tuple[int, int]] = {}  # {topic: (correct, total)}
            
            # Get all quiz attempts
            for session in sessions:
                if session.session_type != "quiz" or not session.topics:
                    continue
                    
                attempts = await self.db.get_attempts_by_session(session.id)
                
                # Group attempts by topic
                for topic in session.topics:
                    if topic not in topic_scores:
                        topic_scores[topic] = (0, 0)
                        
                    correct, total = topic_scores[topic]
                    topic_attempts = [a for a in attempts if a.question_id.startswith(topic)]
                    
                    topic_correct = sum(1 for a in topic_attempts if a.is_correct)
                    topic_total = len(topic_attempts)
                    
                    topic_scores[topic] = (correct + topic_correct, total + topic_total)
            
            # Calculate daily scores
            daily_scores: Dict[datetime, Tuple[int, int]] = {}  # {date: (correct, total)}
            
            for session in sessions:
                if session.session_type != "quiz":
                    continue
                    
                date = session.start_time.replace(hour=0, minute=0, second=0, microsecond=0)
                
                if date not in daily_scores:
                    daily_scores[date] = (0, 0)
                    
                correct, total = daily_scores[date]
                daily_scores[date] = (correct + (session.correct_answers or 0), 
                                      total + (session.total_questions or 0))
            
            # Calculate time spent by activity
            time_distribution: Dict[str, float] = {}  # {activity_type: minutes_spent}
            
            for session in sessions:
                if not session.end_time:
                    continue
                    
                duration = (session.end_time - session.start_time).total_seconds() / 60.0  # minutes
                
                activity = session.session_type.capitalize()
                if activity in time_distribution:
                    time_distribution[activity] += duration
                else:
                    time_distribution[activity] = duration
            
            # Calculate mastery levels
            mastery_levels: Dict[str, int] = {}  # {topic: mastery_level (0-100)}
            
            for topic, (correct, total) in topic_scores.items():
                if total > 0:
                    # Simple mastery calculation based on accuracy and number of questions
                    accuracy_factor = correct / total
                    quantity_factor = min(1.0, total / 20)  # Max out at 20 questions per topic
                    mastery = int(accuracy_factor * quantity_factor * 100)
                    mastery_levels[topic] = mastery
            
            # Calculate difficulty comparison
            difficulty_scores: Dict[str, Dict[str, float]] = {
                "easy": {}, "medium": {}, "hard": {}
            }
            
            for session in sessions:
                if session.session_type != "quiz" or not session.difficulty:
                    continue
                    
                difficulty = session.difficulty.value
                
                for topic in session.topics:
                    if topic not in difficulty_scores[difficulty]:
                        difficulty_scores[difficulty][topic] = 0.0
                        
                    # Get attempts for this session and topic
                    attempts = await self.db.get_attempts_by_session(session.id)
                    topic_attempts = [a for a in attempts if a.question_id.startswith(topic)]
                    
                    if topic_attempts:
                        correct = sum(1 for a in topic_attempts if a.is_correct)
                        accuracy = (correct / len(topic_attempts)) * 100
                        
                        # Update with weighted average
                        current = difficulty_scores[difficulty][topic]
                        difficulty_scores[difficulty][topic] = accuracy if current == 0 else (current + accuracy) / 2
            
            # Generate charts based on available data
            charts = []
            chart_files = []
            
            # 1. Accuracy by Topic Chart
            if topic_scores:
                topic_chart = self.visualizer.generate_accuracy_chart(topic_scores)
                charts.append(("topic_accuracy.png", topic_chart))
                
            # 2. Progress Over Time Chart
            if len(daily_scores) > 1:
                progress_chart = self.visualizer.generate_progress_chart(daily_scores)
                charts.append(("progress.png", progress_chart))
                
            # 3. Study Time Distribution
            if time_distribution:
                time_chart = self.visualizer.generate_time_distribution_chart(time_distribution)
                charts.append(("time_distribution.png", time_chart))
                
            # 4. Topic Mastery Levels
            if len(mastery_levels) >= 3:
                mastery_chart = self.visualizer.generate_mastery_chart(mastery_levels)
                charts.append(("mastery.png", mastery_chart))
                
            # 5. Performance by Difficulty
            difficulty_data = {d: scores for d, scores in difficulty_scores.items() if scores}
            if len(difficulty_data) > 1:
                difficulty_chart = self.visualizer.generate_difficulty_comparison(difficulty_data)
                charts.append(("difficulty.png", difficulty_chart))
            
            # Create files for each chart
            for filename, chart_data in charts:
                file = discord.File(io.BytesIO(chart_data), filename=filename)
                chart_files.append(file)
            
            # Create summary embed
            embed = discord.Embed(
                title=f"Study Progress for {interaction.user.name}",
                description=f"Overall accuracy: **{accuracy:.1f}%** ({total_correct}/{total_questions} questions)",
                color=discord.Color.blue()
            )
            
            # Add session summary
            quiz_count = sum(1 for s in sessions if s.session_type == "quiz")
            flashcard_count = sum(1 for s in sessions if s.session_type == "flashcard")
            
            embed.add_field(
                name="Study Sessions",
                value=f"Quizzes: {quiz_count}\nFlashcards: {flashcard_count}",
                inline=True
            )
            
            # Add time summary if available
            if time_distribution:
                total_time = sum(time_distribution.values())
                time_text = f"{total_time:.1f} minutes"
                if total_time > 60:
                    hours = total_time / 60
                    time_text = f"{hours:.1f} hours"
                
                embed.add_field(
                    name="Time Spent",
                    value=time_text,
                    inline=True
                )
            
            # Add strongest/weakest topics if available
            if topic_scores:
                sorted_topics = sorted(
                    [(t, c/t) for t, (c, t) in topic_scores.items() if t > 0],
                    key=lambda x: x[1]
                )
                
                if sorted_topics:
                    weakest = sorted_topics[0][0]
                    strongest = sorted_topics[-1][0]
                    
                    embed.add_field(
                        name="Topic Analysis",
                        value=f"Strongest: {strongest}\nWeakest: {weakest}",
                        inline=True
                    )
            
            # Send results with charts
            if chart_files:
                await interaction.followup.send(embed=embed, files=chart_files)
            else:
                await interaction.followup.send(embed=embed)
                
        except Exception as e:
            # Handle errors
            await interaction.followup.send(
                f"Error generating progress analytics: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(
        name="history",
        description="View your study session history for a specific date"
    )
    @app_commands.describe(
        date="Date in YYYY-MM-DD format (default: today)"
    )
    async def history(self, interaction: discord.Interaction, date: Optional[str] = None):
        """Show study session history for a specific date."""
        # Check if user is registered
        user = await self.db.get_user_by_discord_id(str(interaction.user.id))
        if not user:
            await interaction.response.send_message(
                "You need to register first! Use `/register` to get started.",
                ephemeral=True
            )
            return
        
        # Parse date
        target_date = None
        if date:
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                await interaction.response.send_message(
                    "Invalid date format. Please use YYYY-MM-DD format.",
                    ephemeral=True
                )
                return
        else:
            # Default to today
            target_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Defer response
        await interaction.response.defer(thinking=True)
        
        try:
            # Get sessions for the specified date
            sessions = await self.db.get_sessions_by_date(user.id, target_date)
            
            if not sessions:
                await interaction.followup.send(
                    f"No study sessions found for {target_date.strftime('%Y-%m-%d')}.",
                    ephemeral=True
                )
                return
            
            # Create embed to display session history
            embed = discord.Embed(
                title=f"Study History: {target_date.strftime('%Y-%m-%d')}",
                description=f"Found {len(sessions)} study sessions.",
                color=discord.Color.blue()
            )
            
            # Add sessions to embed
            for i, session in enumerate(sorted(sessions, key=lambda s: s.start_time), 1):
                # Get material title
                material = await self.db.get_material_by_id(session.material_id)
                material_title = material.title if material else "Unknown Material"
                
                # Format session details
                start_time = session.start_time.strftime("%H:%M")
                duration = "N/A"
                
                if session.end_time:
                    duration_secs = (session.end_time - session.start_time).total_seconds()
                    minutes, seconds = divmod(int(duration_secs), 60)
                    duration = f"{minutes}m {seconds}s"
                
                # Get session details
                details = [f"Material: {material_title}", f"Duration: {duration}"]
                
                if session.session_type == "quiz":
                    if session.score is not None:
                        details.append(f"Score: {session.score:.1f}%")
                    
                    if session.total_questions:
                        details.append(f"Questions: {session.correct_answers}/{session.total_questions}")
                    
                    if session.difficulty:
                        details.append(f"Difficulty: {session.difficulty.value.capitalize()}")
                
                # Add field for this session
                embed.add_field(
                    name=f"{i}. {session.session_type.capitalize()} at {start_time}",
                    value="\n".join(details),
                    inline=False
                )
            
            # Send the history
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            # Handle errors
            await interaction.followup.send(
                f"Error retrieving session history: {str(e)}",
                ephemeral=True
            )
