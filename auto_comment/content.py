import requests
from bs4 import BeautifulSoup
from typing import Optional
from .exceptions import ContentExtractionError

class ContentExtractor:
    @staticmethod
    def extract(url: str) -> str:
        """Extract content from the given URL."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup.get_text()
        except requests.RequestException as e:
            raise ContentExtractionError(f"Failed to access URL {url}: {e}")