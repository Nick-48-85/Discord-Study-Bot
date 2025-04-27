"""
Commands for handling study materials in the Discord Adaptive Study Coach.
"""

import os
import uuid
import discord
import datetime
import aiofiles
from discord import app_commands
from discord.ext import commands
from typing import Optional, List
import json

from ..services.database import DatabaseService
from ..services.ollama import OllamaService, PromptType
from ..services.summarization import EnhancedSummarizationService
from ..utils.document import DocumentProcessor
from ..models.models import StudyMaterial


class StudyCommands(commands.Cog):
    """Commands for managing study materials."""
    
    def __init__(self, bot):
        """Initialize study material commands."""
        self.bot = bot
        self.db = bot.db
        self.ollama = bot.ollama
        self.doc_processor = DocumentProcessor()
    
    @app_commands.command(
        name="upload",
        description="Upload study material (PDF, text, or URL)"
    )
    @app_commands.describe(
        file="Upload a PDF or text file",
        url="Link to a webpage with study content",
        text="Paste text content directly",
        title="Optional title for the study material"
    )
    async def upload(
        self, 
        interaction: discord.Interaction, 
        file: Optional[discord.Attachment] = None,
        url: Optional[str] = None,
        text: Optional[str] = None,
        title: Optional[str] = None
    ):
        """Upload study material from various sources."""
        # Check if user is registered
        user = await self.db.get_user_by_discord_id(str(interaction.user.id))
        if not user:
            await interaction.response.send_message(
                "You need to register first! Use `/register` to get started.",
                ephemeral=True
            )
            return
        
        # Check if at least one source is provided
        if not file and not url and not text:
            await interaction.response.send_message(
                "Please provide a file, URL, or text content to upload.",
                ephemeral=True
            )
            return
        
        # Defer the response since processing might take time
        await interaction.response.defer(thinking=True)
        
        try:
            # Process based on the provided source
            if file:
                # Download the file
                file_data = await file.read()
                file_name = file.filename
                
                # Check file type
                file_ext = os.path.splitext(file_name)[1].lower()
                
                if file_ext == '.pdf':
                    # Process PDF
                    doc_title, content_hash, content_text = await self.doc_processor.process_pdf(
                        file_data, file_name
                    )
                    file_path = await self.doc_processor.save_document(file_data, file_name)
                    content_type = "pdf"
                else:
                    # Process as text
                    text_content = file_data.decode('utf-8', errors='ignore')
                    doc_title, content_hash, content_text = await self.doc_processor.process_text(
                        text_content, os.path.splitext(file_name)[0]
                    )
                    file_path = None
                    content_type = "text"
                
            elif url:
                # Process URL
                doc_title, content_hash, content_text = await self.doc_processor.process_url(url)
                file_path = None
                content_type = "url"
            
            else:  # text
                # Process direct text input
                doc_title, content_hash, content_text = await self.doc_processor.process_text(text, title or "Text Note")
                file_path = None
                content_type = "text"
            
            # Use provided title if available
            if title:
                doc_title = title
            
            # Check if this content already exists (by hash)
            existing_materials = await self.db.get_materials_by_user(user.id)
            for material in existing_materials:
                if material.content_hash == content_hash:
                    await interaction.followup.send(
                        f"This content has already been uploaded as '{material.title}'.",
                        ephemeral=True
                    )
                    return
            
            # Create a new study material entry
            study_material = StudyMaterial(
                id=str(uuid.uuid4()),
                title=doc_title,
                user_id=user.id,
                content_type=content_type,
                content_hash=content_hash,
                content_path=file_path,
                url=url if content_type == "url" else None,
                topics=[],  # Will be populated later with AI extraction
                created_at=datetime.datetime.now()
            )
            
            # Save to database
            await self.db.create_material(study_material)
            
            # Create a success embed
            embed = discord.Embed(
                title="📚 Study Material Uploaded",
                description=f"**{doc_title}** has been successfully added to your study materials!",
                color=discord.Color.green()
            )
            
            embed.add_field(name="Content Type", value=content_type.capitalize(), inline=True)
            embed.add_field(name="Material ID", value=study_material.id[:8] + "...", inline=True)
            
            # Add a preview of the content
            if content_text:
                preview = content_text[:300] + "..." if len(content_text) > 300 else content_text
                embed.add_field(name="Content Preview", value=preview, inline=False)
            
            # Suggest next actions
            embed.add_field(
                name="What's Next?",
                value=(
                    "You can now:\n"
                    "• `/summarize` - Get a concise summary of this material\n"
                    "• `/quiz` - Generate a quiz based on this content\n"
                    "• `/flashcards` - Create flashcards for studying"
                ),
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            # Handle errors
            await interaction.followup.send(
                f"Error processing your study material: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(
        name="materials",
        description="List your uploaded study materials"
    )
    async def materials(self, interaction: discord.Interaction):
        """List all study materials uploaded by the user."""
        # Check if user is registered
        user = await self.db.get_user_by_discord_id(str(interaction.user.id))
        if not user:
            await interaction.response.send_message(
                "You need to register first! Use `/register` to get started.",
                ephemeral=True
            )
            return
        
        # Get all materials for the user
        materials = await self.db.get_materials_by_user(user.id)
        
        if not materials:
            await interaction.response.send_message(
                "You haven't uploaded any study materials yet. Use `/upload` to add some!",
                ephemeral=True
            )
            return
        
        # Create embed to display materials
        embed = discord.Embed(
            title="Your Study Materials",
            description=f"You have {len(materials)} study materials uploaded.",
            color=discord.Color.blue()
        )
        
        # Add each material to the embed
        for i, material in enumerate(materials, 1):
            created_at = material.created_at.strftime("%Y-%m-%d")
            material_type = material.content_type.capitalize()
            
            embed.add_field(
                name=f"{i}. {material.title}",
                value=f"Type: {material_type} | ID: `{material.id[:6]}...` | Added: {created_at}",
                inline=False
            )
            
            # Limit to 25 materials per embed to avoid hitting Discord limits
            if i >= 25:
                embed.set_footer(text="Showing only the first 25 materials.")
                break
        
        await interaction.response.send_message(embed=embed)
    @app_commands.command(
        name="summarize",
        description="Generate a bullet-point summary of study material"
    )
    @app_commands.describe(
        material_id="ID of the study material to summarize (from /materials)",
        points="Number of bullet points to include (default: 10)",
        validation="Enable content validation to prevent hallucinations (default: True)"
    )
    async def summarize(
        self, 
        interaction: discord.Interaction, 
        material_id: str, 
        points: Optional[int] = 10,
        validation: Optional[bool] = True
    ):
        """Generate a summary of study material."""
        # Check if user is registered
        user = await self.db.get_user_by_discord_id(str(interaction.user.id))
        if not user:
            await interaction.response.send_message(
                "You need to register first! Use `/register` to get started.",
                ephemeral=True
            )
            return
        
        # Validate input
        if points < 3 or points > 20:
            await interaction.response.send_message(
                "The number of points must be between 3 and 20.",
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
        
        # Defer the response since processing might take time
        await interaction.response.defer(thinking=True)
        
        try:            # Get the content of the material
            content_text = ""
            
            try:
                if target_material.content_type == "pdf" and target_material.content_path:
                    # Read the PDF text
                    try:
                        from pdfminer.high_level import extract_text
                        content_text = extract_text(target_material.content_path)
                    except ImportError:
                        await interaction.followup.send(
                            "Error: Could not import PDF processing library. Please install 'pdfminer.six'.",
                            ephemeral=True
                        )
                        return
                    
                elif target_material.content_type == "url" and target_material.url:
                    # Process URL content
                    _, _, content_text = await self.doc_processor.process_url(target_material.url)
                    
                else:
                    # For text content, we need to retrieve it from database or cache
                    # This is simplified for now - you might need to adjust based on your storage strategy
                    _, _, content_text = await self.doc_processor.process_text("", target_material.title)
                    
                if not content_text or len(content_text.strip()) < 50:
                    await interaction.followup.send(
                        "Error: Could not extract sufficient content from the study material.",
                        ephemeral=True
                    )
                    return
            except Exception as e:
                await interaction.followup.send(
                    f"Error accessing study material content: {str(e)}",
                    ephemeral=True
                )
                return
            
            # Use the EnhancedSummarizationService from the bot
            summarization_service = self.bot.summarization_service
            
            # Use the enhanced summarization service with validation
            summary_result = await summarization_service.summarize_document(
                document_text=content_text,
                max_points=points,
                validation_enabled=validation
            )
            
            # Extract the summary points
            summary_points = summary_result.get("summary", [])            # If no summary points, send a clear message
            if not summary_points or not any(summary_points):
                await interaction.followup.send(
                    "Sorry, I couldn't generate a summary for this material. Please try again later or with different content.",
                    ephemeral=True
                )
                return

            # Get detected topics
            topics = summary_result.get("topics", {})
            subject_areas = topics.get("subject_areas", [])
            key_topics = topics.get("key_topics", [])

            # Create enriched embed with topic information
            embed = discord.Embed(
                title=f"📝 Summary: {target_material.title}",
                description="Here's a concise summary of your study material:",
                color=discord.Color.blue()
            )
            
            # Add topic information if available
            if subject_areas or key_topics:
                topic_text = ""
                if subject_areas:
                    topic_text += f"**Subject Areas**: {', '.join(subject_areas)}\n"
                if key_topics:
                    topic_text += f"**Key Topics**: {', '.join(key_topics)}"
                embed.add_field(name="Document Topics", value=topic_text, inline=False)
                
            # Add validation info if available
            if validation and "validation" in summary_result:
                validation_data = summary_result["validation"]
                valid_count = validation_data.get("total_points", 0) - validation_data.get("invalid_points_count", 0)
                total_count = validation_data.get("total_points", 0)
                
                if "regenerated" in summary_result and summary_result["regenerated"]:
                    validation_text = f"⚠️ Initial summary contained inaccuracies. A new, verified summary was generated."
                elif "filtered" in summary_result and summary_result["filtered"]:
                    validation_text = f"⚠️ Some points were filtered out for accuracy. Showing {valid_count} validated points."
                else:
                    validation_text = f"✅ {valid_count}/{total_count} points verified from document content."
                    
                embed.add_field(name="Content Validation", value=validation_text, inline=False)

            # Split summary points into multiple fields if needed to stay within Discord's limits
            # Discord has a 1024 character limit per field
            current_field = []
            current_length = 0
            field_count = 1
            FIELD_LIMIT = 1024

            for point in summary_points:
                # Truncate individual points if needed
                if len(point) > 1000:
                    point = point[:997] + "..."
                point_text = f"• {point}"
                if current_length + len(point_text) + 1 > FIELD_LIMIT:  # +1 for newline
                    # Add current field and start a new one
                    field_name = "Key Points" if field_count == 1 else f"Key Points (continued {field_count})"
                    embed.add_field(name=field_name, value="\n".join(current_field), inline=False)
                    current_field = [point_text]
                    current_length = len(point_text)
                    field_count += 1
                else:
                    current_field.append(point_text)
                    current_length += len(point_text) + 1  # +1 for newline

            # Add the last field if there are any remaining points
            if current_field:
                field_name = "Key Points" if field_count == 1 else f"Key Points (continued {field_count})"
                embed.add_field(name=field_name, value="\n".join(current_field), inline=False)

            # Add footer with metadata
            embed.set_footer(text=f"Material ID: {target_material.id[:6]}... | Generated: {datetime.datetime.now().strftime('%Y-%m-%d')}")

            # Send the summary
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            import traceback
            print("Error generating summary:", traceback.format_exc())
            await interaction.followup.send(
                f"Error generating summary: {str(e)}",
                ephemeral=True
            )
