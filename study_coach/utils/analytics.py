"""
Utilities for generating analytics visualizations.
"""

import io
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict, Any, Tuple, Optional
from matplotlib.figure import Figure
from datetime import datetime, timedelta


class AnalyticsVisualizer:
    """Utility for generating analytics visualizations."""
    
    @staticmethod
    def generate_accuracy_chart(
        topic_scores: Dict[str, Tuple[int, int]],  # {topic: (correct, total)}
        title: str = "Accuracy By Topic"
    ) -> bytes:
        """Generate a bar chart showing accuracy by topic."""
        # Sort topics by accuracy
        topics = []
        accuracy = []
        
        for topic, (correct, total) in topic_scores.items():
            if total > 0:  # Avoid division by zero
                topics.append(topic)
                accuracy.append((correct / total) * 100)
        
        # Sort for better visualization
        sorted_indices = np.argsort(accuracy)
        topics = [topics[i] for i in sorted_indices]
        accuracy = [accuracy[i] for i in sorted_indices]
        
        # Create the figure
        plt.figure(figsize=(10, 6))
        plt.barh(topics, accuracy, color='skyblue')
        plt.xlabel('Accuracy (%)')
        plt.ylabel('Topic')
        plt.title(title)
        plt.xlim(0, 100)
        plt.grid(axis='x', linestyle='--', alpha=0.7)
        
        # Add percentage labels
        for i, v in enumerate(accuracy):
            plt.text(v + 1, i, f"{v:.1f}%", va='center')
        
        # Save to bytes
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close()
        buf.seek(0)
        
        return buf.getvalue()
    
    @staticmethod
    def generate_progress_chart(
        daily_scores: Dict[datetime, Tuple[int, int]],  # {date: (correct, total)}
        title: str = "Daily Progress"
    ) -> bytes:
        """Generate a line chart showing progress over time."""
        # Sort dates
        dates = sorted(daily_scores.keys())
        
        # Calculate accuracy
        accuracy = [(daily_scores[d][0] / daily_scores[d][1]) * 100 if daily_scores[d][1] > 0 else 0 for d in dates]
        
        # Format dates for display
        date_labels = [d.strftime('%m/%d') for d in dates]
        
        # Create the figure
        plt.figure(figsize=(10, 6))
        plt.plot(date_labels, accuracy, marker='o', linestyle='-', color='royalblue')
        plt.xlabel('Date')
        plt.ylabel('Accuracy (%)')
        plt.title(title)
        plt.ylim(0, 100)
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # Add a trend line if there are enough data points
        if len(dates) > 2:
            z = np.polyfit(range(len(dates)), accuracy, 1)
            p = np.poly1d(z)
            plt.plot(date_labels, p(range(len(dates))), "r--", alpha=0.7)
        
        # Save to bytes
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close()
        buf.seek(0)
        
        return buf.getvalue()
    
    @staticmethod
    def generate_time_distribution_chart(
        session_times: Dict[str, float],  # {activity_type: total_minutes}
        title: str = "Study Time Distribution"
    ) -> bytes:
        """Generate a pie chart showing distribution of study time."""
        # Sort by time spent
        labels = list(session_times.keys())
        sizes = list(session_times.values())
        
        # Create the figure
        plt.figure(figsize=(8, 8))
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, 
                shadow=True, explode=[0.05] * len(labels))
        plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        plt.title(title)
        
        # Save to bytes
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close()
        buf.seek(0)
        
        return buf.getvalue()
    
    @staticmethod
    def generate_mastery_chart(
        mastery_levels: Dict[str, int],  # {topic: mastery_level (0-100)}
        title: str = "Topic Mastery Levels"
    ) -> bytes:
        """Generate a radar chart showing mastery levels across topics."""
        topics = list(mastery_levels.keys())
        levels = list(mastery_levels.values())
        
        # Create a radar chart
        angles = np.linspace(0, 2*np.pi, len(topics), endpoint=False).tolist()
        levels += [levels[0]]  # Close the loop
        angles += [angles[0]]  # Close the loop
        topics += [topics[0]]  # Close the loop
        
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
        ax.plot(angles, levels, 'o-', linewidth=2, color='royalblue')
        ax.fill(angles, levels, alpha=0.25, color='royalblue')
        ax.set_thetagrids(np.degrees(angles[:-1]), topics[:-1])
        ax.set_ylim(0, 100)
        ax.set_title(title)
        ax.grid(True)
        
        # Save to bytes
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close()
        buf.seek(0)
        
        return buf.getvalue()
    
    @staticmethod
    def generate_difficulty_comparison(
        difficulty_scores: Dict[str, Dict[str, float]],  # {difficulty: {topic: accuracy}}
        title: str = "Performance by Difficulty Level"
    ) -> bytes:
        """Generate a grouped bar chart comparing performance across difficulty levels."""
        # Get all topics
        all_topics = set()
        for diff, scores in difficulty_scores.items():
            all_topics.update(scores.keys())
        all_topics = list(all_topics)
        
        # Set width of bars
        barWidth = 0.25
        
        # Set position of bar on x-axis
        positions = {}
        bars = []
        
        # Create the figure
        plt.figure(figsize=(12, 8))
        
        # Plot each difficulty level
        for i, (diff, scores) in enumerate(difficulty_scores.items()):
            pos = [j + barWidth * i for j in range(len(all_topics))]
            positions[diff] = pos
            
            # Get scores for each topic (or 0 if missing)
            diff_scores = [scores.get(topic, 0) for topic in all_topics]
            
            # Create bars
            bar = plt.bar(pos, diff_scores, width=barWidth, edgecolor='grey', 
                          label=diff.capitalize())
            bars.append(bar)
        
        # Add labels and legend
        plt.xlabel('Topic', fontweight='bold')
        plt.ylabel('Accuracy (%)', fontweight='bold')
        plt.title(title)
        plt.xticks([p + barWidth for p in range(len(all_topics))], all_topics, rotation=45, ha='right')
        plt.legend()
        
        # Save to bytes
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.5)
        plt.close()
        buf.seek(0)
        
        return buf.getvalue()
