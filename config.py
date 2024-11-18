# config.py
from dotenv import load_dotenv
import os
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Flask app secret key
SECRET_KEY = os.getenv('SECRET_KEY', 'any-secret-key')

# API Keys
TMDB_API_KEY = os.getenv('TMDB_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
AI_GATEWAY_ENDPOINT = os.getenv('AI_GATEWAY_ENDPOINT', None)

def verify_tmdb_api_key():
    """Verify TMDB API key is working"""
    try:
        response = requests.get(
            'https://api.themoviedb.org/3/movie/popular',
            headers={'Authorization': f'Bearer {TMDB_API_KEY}'}
        )
        if response.status_code == 200:
            logger.info("TMDB API key verified successfully")
            return True
        else:
            logger.error(f"TMDB API key verification failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error verifying TMDB API key: {e}")
        return False

if not TMDB_API_KEY or not OPENAI_API_KEY:
    raise ValueError("Missing required API keys in environment variables")

# Verify TMDB API key on startup
if not verify_tmdb_api_key():
    raise ValueError("Invalid TMDB API key")