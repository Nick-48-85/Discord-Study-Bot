"""
Utilities for processing different document types.
"""

import os
import io
import uuid
import hashlib
import aiofiles
import httpx
from typing import Tuple, List, Dict, Any, Optional
from pdfminer.high_level import extract_text
from bs4 import BeautifulSoup


class DocumentProcessor:
    """Utility for processing different document types."""
    
    def __init__(self, storage_dir: str = "study_materials"):
        """Initialize the document processor."""
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
    
    async def process_url(self, url: str) -> Tuple[str, str, str]:
        """Process content from a URL."""
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            content = response.text
            
            # Generate content hash
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            # Extract title
            try:
                soup = BeautifulSoup(content, 'html.parser')
                title = soup.title.string if soup.title else url.split('/')[-1]
                
                # Extract main text content
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.extract()
                
                # Get text content
                text = soup.get_text(separator=' ', strip=True)
                
                return title, content_hash, text
            except Exception as e:
                return url.split('/')[-1], content_hash, content
    
    async def process_pdf(self, file_data: bytes, filename: str) -> Tuple[str, str, str]:
        """Process a PDF document."""
        # Generate a unique filename for storage
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(self.storage_dir, unique_filename)
        
        # Save the file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_data)
        
        # Extract text
        text = extract_text(file_path)
        
        # Generate content hash
        content_hash = hashlib.md5(file_data).hexdigest()
        
        # Use filename without extension as title
        title = os.path.splitext(filename)[0]
        
        return title, content_hash, text
    
    async def process_text(self, text: str, title: str = "Untitled Document") -> Tuple[str, str, str]:
        """Process plain text."""
        # Generate content hash
        content_hash = hashlib.md5(text.encode()).hexdigest()
        
        return title, content_hash, text
    
    async def save_document(self, content: bytes, filename: str) -> str:
        """Save document content to file system and return the file path."""
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(self.storage_dir, unique_filename)
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
            
        return file_path
