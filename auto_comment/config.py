import logging
import openai
from typing import Optional

class OpenAIConfig:
    _instance = None
    
    def __init__(self):
        self.baseurl: Optional[str] = None
        self.apikey: Optional[str] = None
        self.model: Optional[str] = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = OpenAIConfig()
        return cls._instance

    def is_initialized(self) -> bool:
        return all([self.baseurl, self.apikey, self.model])

def init_openai(baseurl: str, apikey: str, model: str) -> None:
    """Initialize OpenAI configuration."""
    if not all([baseurl, apikey, model]):
        raise ValueError("Missing initialization parameters")
    
    config = OpenAIConfig.get_instance()
    config.baseurl = baseurl
    config.apikey = apikey
    config.model = model
    
    openai.api_base = baseurl
    openai.api_key = apikey