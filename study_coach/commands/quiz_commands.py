"""
Commands for quiz functionality in the Discord Adaptive Study Coach.
"""

import discord
import uuid
import datetime
import asyncio
from discord import app_commands, ui
from discord.ext import commands
from typing import Optional, List, Dict, Any, Union

from ..services.database import DatabaseService
from ..services.ollama import OllamaService
from ..models.models import (
    UserProfile, StudyMaterial, QuizQuestion, 
    QuizAttempt, StudySession, DifficultyLevel
)


class QuizView(ui.View):
    """Interactive view for quizzes."""
    
    def __init__(self, questions: List[Dict[str, Any]], session_id: str, user_id: str, db_service: DatabaseService):
        super().__init__(timeout=1800)  # 30-minute timeout
        self.questions = questions
        self.current_question = 0
        self.session_id = session_id
        self.user_id = user_id
        self.db = db_service
        self.correct_count = 0
        self.total_count = 0
        self.start_time = datetime.datetime.now()
        self.question_start_time = self.start_time
        self.reaction_times = []
        
        # Add buttons for multiple-choice questions
        if questions and questions[0]["type"] == "multiple_choice":
            self.add_option_buttons()
    
    def add_option_buttons(self):
        """Add option buttons for multiple-choice questions."""
        # Clear existing buttons first
        for item in self.children.copy():
            self.remove_item(item)
        
        # Add one button per option
        options = ["A", "B", "C", "D"]
        for i, option in enumerate(options):
            button = ui.Button(label=option, style=discord.ButtonStyle.secondary, custom_id=str(i))
            button.callback = self.make_answer_callback(i)
            self.add_item(button)
    
    def make_answer_callback(self, option_index: int):
        """Create a callback for an answer button."""
        async def answer_callback(interaction: discord.Interaction):
            # Verify the user
            if str(interaction.user.id) != self.user_id:
                await interaction.response.send_message(
                    "This isn't your quiz session!", ephemeral=True
                )
                return
            
            # Calculate time taken
            time_taken = (datetime.datetime.now() - self.question_start_time).total_seconds()
            self.reaction_times.append(time_taken)
            
            current_q = self.questions[self.current_question]
            is_correct = option_index == current_q["correct_answer"]
            
            # Record the attempt
            attempt = QuizAttempt(
                id=str(uuid.uuid4()),
                user_id=self.user_id,
                question_id=current_q.get("id", f"temp-{uuid.uuid4()}"),
                answer=option_index,
                is_correct=is_correct,
                time_taken_seconds=time_taken,
                session_id=self.session_id,
                created_at=datetime.datetime.now()
            )
            
            await self.db.create_attempt(attempt)
            
            # Update statistics
            if is_correct:
                self.correct_count += 1
            self.total_count += 1
            
            # Create response embed
            embed = discord.Embed(
                title=current_q["question"],
                color=discord.Color.green() if is_correct else discord.Color.red()
            )
            
            options = current_q["options"]
            for i, opt in enumerate(options):
                prefix = "✅ " if i == current_q["correct_answer"] else "❌ " if i == option_index else ""
                embed.add_field(
                    name=f"{chr(65 + i)}", 
                    value=f"{prefix}{opt}",
                    inline=False
                )
            
            embed.set_footer(text=f"Question {self.current_question + 1}/{len(self.questions)}")
            
            # Disable the buttons after answering
            for item in self.children:
                item.disabled = True
            
            await interaction.response.edit_message(embed=embed, view=self)
            
            # Proceed to next question or finish quiz
            self.current_question += 1
            
            if self.current_question < len(self.questions):
                # Reset question start time for the next question
                self.question_start_time = datetime.datetime.now()
                await asyncio.sleep(2)  # Brief pause to see the result
                await self.show_next_question(interaction)
            else:
                # Quiz finished
                await self.finish_quiz(interaction)
        
        return answer_callback
    
    async def show_next_question(self, interaction: discord.Interaction):
        """Show the next question."""
        q = self.questions[self.current_question]
        
        embed = discord.Embed(
            title=q["question"],
            color=discord.Color.blue()
        )
        
        if q["type"] == "multiple_choice":
            for i, option in enumerate(q["options"]):
                embed.add_field(
                    name=f"{chr(65 + i)}", 
                    value=option,
                    inline=False
                )
            
            # Re-enable buttons
            self.add_option_buttons()
        else:
            # Short answer question
            embed.description = "*Type your answer in chat*"
            # No buttons needed
        
        embed.set_footer(text=f"Question {self.current_question + 1}/{len(self.questions)}")
        
        await interaction.edit_original_response(embed=embed, view=self)
    
    async def finish_quiz(self, interaction: discord.Interaction):
        """Finish the quiz and show results."""
        total_time = (datetime.datetime.now() - self.start_time).total_seconds()
        avg_time = sum(self.reaction_times) / len(self.reaction_times) if self.reaction_times else 0
        score_pct = (self.correct_count / self.total_count) * 100 if self.total_count > 0 else 0
        
        # Create results embed
        embed = discord.Embed(
            title="Quiz Results",
            description=f"You've completed the quiz! Here's how you did:",
            color=discord.Color.gold()
        )
        
        embed.add_field(name="Score", value=f"{self.correct_count}/{self.total_count} ({score_pct:.1f}%)", inline=True)
        embed.add_field(name="Time", value=f"{total_time:.1f} seconds", inline=True)
        embed.add_field(name="Avg. Time per Question", value=f"{avg_time:.1f} seconds", inline=True)
        
        # Update the session with final results
        session = await self.db.get_session_by_id(self.session_id)
        if session:
            session.end_time = datetime.datetime.now()
            session.score = score_pct
            session.correct_answers = self.correct_count
            session.total_questions = self.total_count
            
            await self.db.update_session(session)
        
        # Update user profile stats
        user = await self.db.get_user_by_discord_id(self.user_id)
        if user:
            user.total_questions_answered += self.total_count
            user.correct_answers += self.correct_count
            user.session_count += 1
            user.last_active = datetime.datetime.now()
            
            await self.db.update_user(user)
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        await interaction.edit_original_response(embed=embed, view=self)
        
        # Add recommendation button
        recommend_view = ui.View()
        recommend_button = ui.Button(
            label="Get Recommendations", 
            style=discord.ButtonStyle.primary,
            custom_id="recommend"
        )
        
        async def recommend_callback(interaction: discord.Interaction):
            if str(interaction.user.id) != self.user_id:
                return
            
            # Get user data
            user_data = {
                "score": score_pct,
                "reaction_time": avg_time,
                "correct_answers": self.correct_count,
                "total_questions": self.total_count
            }
            
            # Get recent activities
            recent_activities = [
                {"type": "quiz", "score": score_pct, "questions": self.total_count}
            ]
            
            # Generate recommendations
            recommendations = await self.db.bot.ollama.recommend_next_steps(
                user_data, recent_activities
            )
            
            if recommendations:
                rec_embed = discord.Embed(
                    title="Personalized Recommendations",
                    description="Based on your performance, here's what to do next:",
                    color=discord.Color.blue()
                )
                
                for rec in recommendations:
                    rec_embed.add_field(
                        name=rec["title"],
                        value=rec["description"],
                        inline=False
                    )
                
                await interaction.response.send_message(embed=rec_embed, ephemeral=True)
            else:
                await interaction.response.send_message(
                    "I don't have any specific recommendations at this time. Keep practicing!",
                    ephemeral=True
                )
        
        recommend_button.callback = recommend_callback
        recommend_view.add_item(recommend_button)
        
        await interaction.followup.send("Would you like personalized recommendations?", view=recommend_view)


class FlashcardView(ui.View):
    """Interactive view for flashcards."""
    
    def __init__(self, flashcards: List[Dict[str, str]], session_id: str, user_id: str):
        super().__init__(timeout=1800)  # 30-minute timeout
        self.flashcards = flashcards
        self.current_card = 0
        self.session_id = session_id
        self.user_id = user_id
        self.showing_front = True
        self.start_time = datetime.datetime.now()
    
    @ui.button(label="Flip", style=discord.ButtonStyle.primary)
    async def flip_card(self, interaction: discord.Interaction, button: ui.Button):
        """Flip the current flashcard."""
        # Verify the user
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message(
                "This isn't your flashcard session!", ephemeral=True
            )
            return
        
        self.showing_front = not self.showing_front
        await self.update_card(interaction)
    
    @ui.button(label="Previous", style=discord.ButtonStyle.secondary)
    async def previous_card(self, interaction: discord.Interaction, button: ui.Button):
        """Go to the previous flashcard."""
        # Verify the user
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message(
                "This isn't your flashcard session!", ephemeral=True
            )
            return
        
        if self.current_card > 0:
            self.current_card -= 1
            self.showing_front = True
            await self.update_card(interaction)
        else:
            await interaction.response.send_message(
                "You're already at the first card!", ephemeral=True
            )
    
    @ui.button(label="Next", style=discord.ButtonStyle.secondary)
    async def next_card(self, interaction: discord.Interaction, button: ui.Button):
        """Go to the next flashcard."""
        # Verify the user
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message(
                "This isn't your flashcard session!", ephemeral=True
            )
            return
        
        if self.current_card < len(self.flashcards) - 1:
            self.current_card += 1
            self.showing_front = True
            await self.update_card(interaction)
        else:
            await interaction.response.send_message(
                "You've reached the last card! Use the 'Finish' button to end the session.",
                ephemeral=True
            )
    
    @ui.button(label="Finish", style=discord.ButtonStyle.danger)
    async def finish_flashcards(self, interaction: discord.Interaction, button: ui.Button):
        """Finish the flashcard session."""
        # Verify the user
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message(
                "This isn't your flashcard session!", ephemeral=True
            )
            return
        
        total_time = (datetime.datetime.now() - self.start_time).seconds
        
        # Create results embed
        embed = discord.Embed(
            title="Flashcard Session Complete",
            description="You've finished reviewing your flashcards!",
            color=discord.Color.gold()
        )
        
        embed.add_field(name="Cards Reviewed", value=str(len(self.flashcards)), inline=True)
        embed.add_field(name="Time Spent", value=f"{total_time // 60}m {total_time % 60}s", inline=True)
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def update_card(self, interaction: discord.Interaction):
        """Update the flashcard display."""
        card = self.flashcards[self.current_card]
        
        if self.showing_front:
            # Show the front (question)
            embed = discord.Embed(
                title=f"Flashcard {self.current_card + 1}/{len(self.flashcards)}",
                description=card["front"],
                color=discord.Color.blue()
            )
            embed.set_footer(text="Click 'Flip' to see the answer")
        else:
            # Show the back (answer)
            embed = discord.Embed(
                title=f"Flashcard {self.current_card + 1}/{len(self.flashcards)}",
                description=card["back"],
                color=discord.Color.green()
            )
            embed.set_footer(text="Click 'Flip' to see the question again")
        
        if "topic" in card:
            embed.add_field(name="Topic", value=card["topic"], inline=True)
        
        await interaction.response.edit_message(embed=embed, view=self)


class QuizCommands(commands.Cog):
    """Commands for quiz functionality."""
    
    def __init__(self, bot):
        """Initialize quiz commands."""
        self.bot = bot
        self.db = bot.db
        self.ollama = bot.ollama
    
    @app_commands.command(
        name="quiz",
        description="Generate a quiz based on your study materials"
    )
    @app_commands.describe(
        material_id="ID of the study material for the quiz (from /materials)",
        question_count="Number of questions to include (default: 5)",
        question_type="Type of questions to generate",
        difficulty="Difficulty level for the questions"
    )
    @app_commands.choices(
        question_type=[
            app_commands.Choice(name="Multiple Choice", value="multiple_choice"),
            app_commands.Choice(name="Short Answer", value="short_answer"),
        ],
        difficulty=[
            app_commands.Choice(name="Easy", value="easy"),
            app_commands.Choice(name="Medium", value="medium"),
            app_commands.Choice(name="Hard", value="hard"),
        ]
    )
    async def quiz(
        self, 
        interaction: discord.Interaction, 
        material_id: str,
        question_count: Optional[int] = 5,
        question_type: Optional[app_commands.Choice[str]] = None,
        difficulty: Optional[app_commands.Choice[str]] = None
    ):
        """Generate and start a quiz session."""
        # Check if user is registered
        user = await self.db.get_user_by_discord_id(str(interaction.user.id))
        if not user:
            await interaction.response.send_message(
                "You need to register first! Use `/register` to get started.",
                ephemeral=True
            )
            return
        
        # Validate inputs
        if question_count < 1 or question_count > 15:
            await interaction.response.send_message(
                "The number of questions must be between 1 and 15.",
                ephemeral=True
            )
            return
        
        # Set defaults if not provided
        q_type = question_type.value if question_type else "multiple_choice"
        diff = difficulty.value if difficulty else user.difficulty_preference.value
        
        # Find the study material
        materials = await self.db.get_materials_by_user(user.id)
        target_material = None
        
        for material in materials:
            if material.id.startswith(material_id):
                target_material = material
                break
        
        if not target_material:
            await interaction.response.send_message(
                f"Couldn't find a study material with ID starting with '{material_id}'. "
                f"Use `/materials` to see your materials and their IDs.",
                ephemeral=True
            )
            return
        
        # Defer the response since quiz generation might take time
        await interaction.response.defer(thinking=True)
        
        try:
            # Get the content of the material
            content_text = ""
            
            if target_material.content_type == "pdf" and target_material.content_path:
                # Read the PDF text
                from pdfminer.high_level import extract_text
                content_text = extract_text(target_material.content_path)
                
            elif target_material.content_type == "url" and target_material.url:
                # Process URL content
                _, _, content_text = await self.bot.doc_processor.process_url(target_material.url)
                
            else:
                # For text content, simplified approach
                _, _, content_text = await self.bot.doc_processor.process_text("", target_material.title)
            
            # Generate quiz questions
            questions = await self.ollama.generate_quiz_questions(
                text=content_text,
                num_questions=question_count,
                question_type=q_type,
                difficulty=diff,
                topics=target_material.topics if target_material.topics else None
            )
            
            if not questions:
                await interaction.followup.send(
                    "Sorry, I couldn't generate any quiz questions from this material. "
                    "Try with different content or settings.",
                    ephemeral=True
                )
                return
            
            # Create a study session
            session = StudySession(
                id=str(uuid.uuid4()),
                user_id=user.id,
                material_id=target_material.id,
                session_type="quiz",
                start_time=datetime.datetime.now(),
                difficulty=DifficultyLevel(diff),
                topics=target_material.topics
            )
            
            session_id = await self.db.create_session(session)
            
            # Create database entries for each question
            db_questions = []
            for q in questions:
                question = QuizQuestion(
                    id=str(uuid.uuid4()),
                    material_id=target_material.id,
                    question=q["question"],
                    question_type=q_type,
                    options=q.get("options", []),
                    correct_answer=q["correct_answer"],
                    topic=q.get("topic", None),
                    difficulty=DifficultyLevel(diff)
                )
                db_questions.append(question)
                # Add ID to the question dict for reference
                q["id"] = question.id
            
            await self.db.create_questions_batch(db_questions)
            
            # Start the quiz
            view = QuizView(questions, session_id, str(interaction.user.id), self.db)
            
            # Show the first question
            q = questions[0]
            embed = discord.Embed(
                title=q["question"],
                color=discord.Color.blue()
            )
            
            if q_type == "multiple_choice":
                for i, option in enumerate(q["options"]):
                    embed.add_field(
                        name=f"{chr(65 + i)}", 
                        value=option,
                        inline=False
                    )
            else:
                embed.description = "*Type your answer in chat*"
            
            embed.set_footer(text=f"Question 1/{len(questions)}")
            
            await interaction.followup.send(embed=embed, view=view)
            
        except Exception as e:
            # Handle errors
            await interaction.followup.send(
                f"Error generating quiz: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(
        name="flashcards",
        description="Create flashcards from your study materials"
    )
    @app_commands.describe(
        material_id="ID of the study material for flashcards (from /materials)",
        card_count="Number of flashcards to include (default: 10)"
    )
    async def flashcards(
        self, 
        interaction: discord.Interaction, 
        material_id: str,
        card_count: Optional[int] = 10
    ):
        """Generate and start a flashcard session."""
        # Check if user is registered
        user = await self.db.get_user_by_discord_id(str(interaction.user.id))
        if not user:
            await interaction.response.send_message(
                "You need to register first! Use `/register` to get started.",
                ephemeral=True
            )
            return
        
        # Validate inputs
        if card_count < 1 or card_count > 20:
            await interaction.response.send_message(
                "The number of flashcards must be between 1 and 20.",
                ephemeral=True
            )
            return
        
        # Find the study material
        materials = await self.db.get_materials_by_user(user.id)
        target_material = None
        
        for material in materials:
            if material.id.startswith(material_id):
                target_material = material
                break
        
        if not target_material:
            await interaction.response.send_message(
                f"Couldn't find a study material with ID starting with '{material_id}'. "
                f"Use `/materials` to see your materials and their IDs.",
                ephemeral=True
            )
            return
        
        # Defer the response since flashcard generation might take time
        await interaction.response.defer(thinking=True)
        
        try:
            # Get the content of the material
            content_text = ""
            
            if target_material.content_type == "pdf" and target_material.content_path:
                # Read the PDF text
                from pdfminer.high_level import extract_text
                content_text = extract_text(target_material.content_path)
                
            elif target_material.content_type == "url" and target_material.url:
                # Process URL content
                _, _, content_text = await self.bot.doc_processor.process_url(target_material.url)
                
            else:
                # For text content, simplified approach
                _, _, content_text = await self.bot.doc_processor.process_text("", target_material.title)
            
            # Generate flashcards
            flashcards = await self.ollama.generate_flashcards(
                text=content_text,
                num_cards=card_count,
                topics=target_material.topics if target_material.topics else None
            )
            
            if not flashcards:
                await interaction.followup.send(
                    "Sorry, I couldn't generate any flashcards from this material. "
                    "Try with different content.",
                    ephemeral=True
                )
                return
            
            # Create a study session
            session = StudySession(
                id=str(uuid.uuid4()),
                user_id=user.id,
                material_id=target_material.id,
                session_type="flashcard",
                start_time=datetime.datetime.now(),
                topics=target_material.topics
            )
            
            session_id = await self.db.create_session(session)
            
            # Start the flashcard session
            view = FlashcardView(flashcards, session_id, str(interaction.user.id))
            
            # Show the first card
            first_card = flashcards[0]
            embed = discord.Embed(
                title=f"Flashcard 1/{len(flashcards)}",
                description=first_card["front"],
                color=discord.Color.blue()
            )
            
            if "topic" in first_card:
                embed.add_field(name="Topic", value=first_card["topic"], inline=True)
                
            embed.set_footer(text="Click 'Flip' to see the answer")
            
            await interaction.followup.send(embed=embed, view=view)
            
        except Exception as e:
            # Handle errors
            await interaction.followup.send(
                f"Error generating flashcards: {str(e)}",
                ephemeral=True
            )
