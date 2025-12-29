"""
Guide ingestion - Fetch and parse migration guides from various sources.

Supports:
- URLs (HTML documentation)
- Local Markdown files
- Local text files
- PDF files (future enhancement)
- Recursive link following for related documentation
"""

import re
from pathlib import Path
from typing import List, Optional, Set
from urllib.parse import urljoin, urlparse, urlunparse

import requests


class GuideIngester:
    """Fetch and parse migration guides from various sources."""

    def __init__(self, follow_links: bool = False, max_depth: int = 2):
        """
        Initialize the guide ingester with a cache.

        Args:
            follow_links: If True, follow related documentation links
            max_depth: Maximum depth for recursive link following (default: 2)
        """
        self._cache = {}
        self._visited_urls: Set[str] = set()
        self.follow_links = follow_links
        self.max_depth = max_depth

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

    def ingest_url(self, url: str, depth: int = 0) -> Optional[str]:
        """
        Fetch and convert HTML/PDF from URL to clean text.

        Args:
            url: URL to migration guide
            depth: Current recursion depth for link following

        Returns:
            Clean markdown text or None if fetch fails
        """
        # Normalize URL
        url = self._normalize_url(url)

        # Check if already visited
        if url in self._visited_urls:
            return None

        # Mark as visited
        self._visited_urls.add(url)

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
            print(f"{'  ' * depth}Fetching: {url}")
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

                # Extract related links before removing elements
                related_links = []
                if self.follow_links and depth < self.max_depth:
                    related_links = self._extract_related_links(soup, url)

                # Remove script and style elements
                for script in soup(['script', 'style', 'nav', 'footer', 'header']):
                    script.decompose()

                # Convert to markdown
                markdown = md(str(soup), heading_style="ATX")

                # Clean up excessive whitespace
                markdown = self._clean_text(markdown)

                # Follow related links if enabled
                if related_links:
                    print(f"{'  ' * depth}Found {len(related_links)} related links")
                    for link in related_links:
                        linked_content = self.ingest_url(link, depth + 1)
                        if linked_content:
                            # Append linked content with a separator
                            markdown += f"\n\n---\n# Content from: {link}\n\n{linked_content}"

                return markdown

        except requests.RequestException as e:
            print(f"Error fetching URL {url}: {e}")
            return None
        except (ValueError, KeyError, AttributeError) as e:
            print(f"Error parsing HTML content from {url}: {e}")
            return None
        except (UnicodeDecodeError, LookupError) as e:
            print(f"Error decoding content from {url}: {e}")
            return None
        except Exception as e:
            # Catch any truly unexpected errors
            print(f"Unexpected error processing {url}: {e}")
            import traceback

            traceback.print_exc()
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

        except (IOError, OSError, PermissionError) as e:
            print(f"Error reading file {file_path}: {e}")
            return None
        except UnicodeDecodeError as e:
            print(f"Error decoding file {file_path} (not valid UTF-8): {e}")
            return None
        except Exception as e:
            # Catch any truly unexpected errors
            print(f"Unexpected error reading file {file_path}: {e}")
            import traceback

            traceback.print_exc()
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
            # If section itself is too large, split it into smaller pieces
            if len(section) > max_chars:
                # Save current chunk if it has content
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""

                # Split large section by paragraphs (double newlines)
                paragraphs = section.split('\n\n')
                temp_chunk = ""

                for para in paragraphs:
                    # If a single paragraph is too large, split it by character count
                    if len(para) > max_chars:
                        # Save current temp_chunk if it has content
                        if temp_chunk:
                            chunks.append(temp_chunk.strip())
                            temp_chunk = ""

                        # Split oversized paragraph into max_chars pieces
                        for i in range(0, len(para), max_chars):
                            para_piece = para[i : i + max_chars]
                            chunks.append(para_piece.strip())
                    elif len(temp_chunk) + len(para) + 2 <= max_chars:
                        temp_chunk += "\n\n" + para if temp_chunk else para
                    else:
                        if temp_chunk:
                            chunks.append(temp_chunk.strip())
                        temp_chunk = para

                # Add remaining temp_chunk to current_chunk
                if temp_chunk:
                    current_chunk = temp_chunk
            elif len(current_chunk) + len(section) <= max_chars:
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
        except (ValueError, TypeError, AttributeError):
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

    def _normalize_url(self, url: str) -> str:
        """
        Normalize URL by removing fragments and trailing slashes.

        Args:
            url: URL to normalize

        Returns:
            Normalized URL
        """
        parsed = urlparse(url)
        # Remove fragment (# anchor)
        normalized = urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path.rstrip('/'),
                parsed.params,
                parsed.query,
                '',  # Remove fragment
            )
        )
        return normalized

    def _extract_related_links(self, soup, base_url: str) -> List[str]:
        """
        Extract migration-related links from HTML.

        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative links

        Returns:
            List of related URLs to follow
        """
        # Return empty list if soup is None (BeautifulSoup not available)
        if soup is None:
            return []

        base_domain = urlparse(base_url).netloc
        related_links = []

        # Keywords that indicate migration-related documentation
        migration_keywords = [
            'release-notes',
            'release_notes',
            'releasenotes',
            'breaking-changes',
            'breaking_changes',
            'breakingchanges',
            'migration',
            'migrate',
            'upgrade',
            'changelog',
            'whats-new',
            'whats_new',
            'whatsnew',
            'v6',
            'version-6',
            'version_6',
        ]

        # Find all links
        for link in soup.find_all('a', href=True):
            href = link['href']

            # Convert relative URLs to absolute
            absolute_url = urljoin(base_url, href)

            # Normalize the URL
            normalized_url = self._normalize_url(absolute_url)

            # Skip if already visited
            if normalized_url in self._visited_urls:
                continue

            # Only follow links from the same domain
            link_domain = urlparse(absolute_url).netloc
            if link_domain != base_domain:
                continue

            # Check if URL path or link text contains migration keywords
            url_path = urlparse(absolute_url).path.lower()
            link_text = link.get_text().lower()

            is_migration_related = any(
                keyword in url_path or keyword in link_text for keyword in migration_keywords
            )

            if is_migration_related:
                related_links.append(normalized_url)

        # Remove duplicates while preserving order
        seen = set()
        unique_links = []
        for link in related_links:
            if link not in seen:
                seen.add(link)
                unique_links.append(link)

        return unique_links
