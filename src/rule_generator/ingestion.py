"""
Guide ingestion - Fetch and parse migration guides from various sources.

Supports:
- URLs (HTML documentation)
- Local Markdown files
- Local text files
- PDF files (future enhancement)
"""
import re
import requests
from typing import Optional, List
from pathlib import Path
from urllib.parse import urlparse


class GuideIngester:
    """Fetch and parse migration guides from various sources."""

    def __init__(self):
        """Initialize the guide ingester with a cache."""
        self._cache = {}

    def ingest(self, source: str) -> Optional[str]:
        """
        Ingest a migration guide from any source.

        Args:
            source: URL, file path, or content string

        Returns:
            Clean text content or None if ingestion fails
        """
        # Check cache first
        if source in self._cache:
            return self._cache[source]

        # Determine source type and ingest accordingly
        if self._is_url(source):
            content = self.ingest_url(source)
        elif self._is_file_path(source):
            content = self.ingest_file(source)
        else:
            # Assume it's raw content
            content = source

        if content:
            # Cache the result
            self._cache[source] = content

        return content

    def ingest_url(self, url: str) -> Optional[str]:
        """
        Fetch and convert HTML/PDF from URL to clean text.

        Args:
            url: URL to migration guide

        Returns:
            Clean markdown text or None if fetch fails
        """
        try:
            # Check if beautifulsoup4 is available
            try:
                from bs4 import BeautifulSoup
                from markdownify import markdownify as md
            except ImportError:
                print("Warning: beautifulsoup4 and markdownify required for URL ingestion")
                print("Install with: pip install -r requirements.txt")
                return None

            # Fetch content
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Check content type
            content_type = response.headers.get('content-type', '').lower()

            if 'pdf' in content_type:
                # PDF handling (future enhancement)
                print(f"Warning: PDF support not yet implemented for {url}")
                return None
            else:
                # Assume HTML
                soup = BeautifulSoup(response.content, 'html.parser')

                # Remove script and style elements
                for script in soup(['script', 'style', 'nav', 'footer', 'header']):
                    script.decompose()

                # Convert to markdown
                markdown = md(str(soup), heading_style="ATX")

                # Clean up excessive whitespace
                markdown = self._clean_text(markdown)

                return markdown

        except requests.RequestException as e:
            print(f"Error fetching URL {url}: {e}")
            return None
        except Exception as e:
            print(f"Error parsing content from {url}: {e}")
            return None

    def ingest_file(self, file_path: str) -> Optional[str]:
        """
        Read local markdown/text file.

        Args:
            file_path: Path to local file

        Returns:
            File content or None if read fails
        """
        path = Path(file_path)

        if not path.exists():
            print(f"Error: File not found: {file_path}")
            return None

        try:
            # Determine file type
            suffix = path.suffix.lower()

            if suffix == '.pdf':
                # PDF handling (future enhancement)
                print(f"Warning: PDF support not yet implemented for {file_path}")
                return None
            elif suffix in ['.md', '.markdown', '.txt']:
                # Read as text
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return self._clean_text(content)
            else:
                # Try reading as text anyway
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return self._clean_text(content)

        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None

    def chunk_content(self, content: str, max_tokens: int = 8000) -> List[str]:
        """
        Split large guides into processable chunks.

        Args:
            content: Full guide content
            max_tokens: Maximum tokens per chunk (approximate)

        Returns:
            List of content chunks
        """
        # Rough estimation: 1 token ≈ 4 characters
        max_chars = max_tokens * 4

        if len(content) <= max_chars:
            return [content]

        # Split by sections (markdown headers)
        sections = re.split(r'\n#{1,3}\s+', content)

        chunks = []
        current_chunk = ""

        for section in sections:
            if len(current_chunk) + len(section) <= max_chars:
                current_chunk += "\n\n" + section
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = section

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _is_url(self, source: str) -> bool:
        """Check if source is a URL."""
        try:
            result = urlparse(source)
            return all([result.scheme, result.netloc])
        except:
            return False

    def _is_file_path(self, source: str) -> bool:
        """Check if source is a file path."""
        # If source contains newlines, it's raw content, not a file path
        if '\n' in source:
            return False
        return Path(source).exists() or source.startswith('/') or source.startswith('.')

    def _clean_text(self, text: str) -> str:
        """
        Clean up text content.

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)

        # Remove common navigation/UI elements
        text = re.sub(r'Skip to (?:main )?content', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Table of Contents?', '', text, flags=re.IGNORECASE)

        return text.strip()
