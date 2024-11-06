# movie_service.py
import json
import re
import requests
from config import TMDB_API_KEY, OPENAI_API_KEY
import logging
import random
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"  # w500 for good quality posters

client = OpenAI(api_key=OPENAI_API_KEY)

def get_tmdb_headers():
    return {
        'Authorization': f'Bearer {TMDB_API_KEY}',
        'Accept': 'application/json'
    }

def get_random_posters(count=10):
    try:
        random_page = random.randint(1, 20)  # Limiting to first 20 pages for better quality
        url = f"{TMDB_BASE_URL}/movie/popular"
        params = {
            'page': random_page,
            'language': 'en-US',
            'include_adult': False
        }
        
        logger.info(f"Making request to: {url}")
        response = requests.get(url, headers=get_tmdb_headers(), params=params, timeout=10)
        response.raise_for_status()
        movies_data = response.json().get('results', [])
        
        # Shuffle and limit to requested count
        random.shuffle(movies_data)
        movies_data = movies_data[:count]
        
        # Gather valid posters only
        posters = [
            {
                'id': movie['id'],
                'title': movie.get('title', 'Unknown Title'),
                'poster_url': f"{TMDB_IMAGE_BASE_URL}{movie['poster_path']}",
                'year': movie.get('release_date', '')[:4],
                'genre_ids': movie.get('genre_ids', []),
                'summary': movie.get('overview', 'No summary available'),
                'vote_average': movie.get('vote_average', 0)
            }
            for movie in movies_data if movie.get('poster_path')
        ]
        
        if not posters:
            raise ValueError("No valid posters found in response")
        
        return posters
        
    except Exception as e:
        logger.error(f"Error fetching posters: {str(e)}")
        raise

def get_worst_rated_movies(count=10, anti_preferences=None):
    try:
        url = f"{TMDB_BASE_URL}/discover/movie"
        params = {
            'language': 'en-US',
            'include_adult': False,
            'page': random.randint(1, 5),
            'vote_count.gte': 50
        }

        if anti_preferences:
            genres_to_use = random.sample(anti_preferences['genres_to_include'], min(2, len(anti_preferences['genres_to_include'])))
            params.update({
                'with_genres': '|'.join(map(str, genres_to_use)),
                'primary_release_date.gte': f"{anti_preferences['min_year']}-01-01",
                'primary_release_date.lte': f"{anti_preferences['max_year']}-12-31",
                'vote_average.lte': min(5.0, anti_preferences.get('vote_average_lte', 5.0)),
                'sort_by': anti_preferences.get('sort_preference', 'vote_average.asc')
            })

        logger.info(f"Fetching worst rated movies with params: {params}")
        response = requests.get(url, headers=get_tmdb_headers(), params=params, timeout=10)
        response.raise_for_status()
        movies_data = response.json().get('results', [])
        
        # Shuffle and limit to requested count
        random.shuffle(movies_data)
        movies_data = movies_data[:count]
        
        # Gather valid posters only
        posters = [
            {
                'id': movie['id'],
                'title': movie.get('title', 'Unknown Title'),
                'poster_url': f"{TMDB_IMAGE_BASE_URL}{movie['poster_path']}",
                'year': movie.get('release_date', '')[:4],
                'genre_ids': movie.get('genre_ids', []),
                'summary': movie.get('overview', 'No summary available'),
                'vote_average': movie.get('vote_average', 0)
            }
            for movie in movies_data if movie.get('poster_path')
        ]
        
        if not posters:
            raise ValueError("No valid posters found for the worst-rated movies request")
        
        return posters

    except Exception as e:
        logger.error(f"Error fetching worst rated movies: {str(e)}")
        raise

def get_movie_details(movie_ids):
    """Fetch detailed information about selected movies"""
    movie_details = []
    for movie_id in movie_ids:
        try:
            response = requests.get(
                f"{TMDB_BASE_URL}/movie/{movie_id}",
                headers=get_tmdb_headers()
            )
            if response.status_code == 200:
                movie_data = response.json()
                movie_details.append({
                    'title': movie_data.get('title'),
                    'genres': [g['name'] for g in movie_data.get('genres', [])],
                    'year': movie_data.get('release_date', '')[:4],
                    'overview': movie_data.get('overview'),
                    'vote_average': movie_data.get('vote_average')
                })
        except Exception as e:
            logger.error(f"Error fetching movie details for {movie_id}: {e}")
    return movie_details

def analyze_preferences(selected_movies):
    """Use OpenAI to analyze user preferences and generate anti-preferences"""
    try:
        # Get detailed information about selected movies
        movie_details = get_movie_details(selected_movies)
        
        logger.info(f"Analyzing preferences for movies: {json.dumps(movie_details, indent=2)}")
        
        # Create a prompt for OpenAI
        prompt = f"""Based on these selected movies:
{json.dumps(movie_details, indent=2)}

Analyze their preferences and create a JSON object of anti-preferences that would help find movies they'd hate.
Consider the genres, themes, styles, and quality of the movies they like and generate the opposite.

Create a JSON object with:
1. genres_to_include: list of TMDB genre IDs they would hate (use actual TMDB genre IDs)
2. min_year and max_year: time period they would dislike
3. keywords: list of themes/elements they would hate (in plain English)
4. vote_average_lte: maximum rating to consider (0-10)
5. sort_preference: either "vote_average.asc" or "popularity.asc"

Use these TMDB genre IDs:
Action: 28
Adventure: 12
Animation: 16
Comedy: 35
Crime: 80
Documentary: 99
Drama: 18
Family: 10751
Fantasy: 14
History: 36
Horror: 27
Music: 10402
Mystery: 9648
Romance: 10749
Science Fiction: 878
TV Movie: 10770
Thriller: 53
War: 10752
Western: 37

Return only the JSON object, no explanation."""

        # Send request to OpenAI API
        truncated_prompt = _truncate_text(prompt)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a movie expert who specializes in finding contrasting movie recommendations and responds in JSON format."},
                {"role": "user", "content": truncated_prompt}
            ]
        )

        # Log raw response for debugging
        logger.info(f"Raw OpenAI response: {response}")

        # Extract JSON content from response
        response_content = response.choices[0].message.content
        json_match = re.search(r'```json\n(.*?)\n```', response_content, re.DOTALL)

        if json_match:
            # Parse the JSON content extracted from code block
            anti_preferences = json.loads(json_match.group(1))
            logger.info(f"Generated anti-preferences: {json.dumps(anti_preferences, indent=2)}")
            return anti_preferences
        else:
            logger.error("OpenAI response did not contain valid JSON in code block format.")
            raise ValueError("No valid JSON found in OpenAI response.")

    except Exception as e:
        logger.error(f"Error analyzing preferences: {str(e)}")
        return {
            "genres_to_include": [35, 27],  # Comedy and Horror as defaults
            "min_year": "1900",
            "max_year": "2024",
            "vote_average_lte": 5.0,
            "sort_preference": "vote_average.asc",
            "keywords": ["low budget", "bad acting", "poor special effects"]
        }

def get_worst_rated_movies(count=10, anti_preferences=None):
    """Get movies based on AI-generated anti-preferences, with a fallback to generic low-rated movies if needed."""
    try:
        url = f"{TMDB_BASE_URL}/discover/movie"
        
        # Base parameters for the initial request using anti-preferences
        params = {
            'language': 'en-US',
            'include_adult': False,
            'page': random.randint(1, 5),
            'vote_count.gte': 50  # Ensures a minimum number of votes
        }

        # Apply anti-preferences if available
        if anti_preferences:
            genres_to_use = random.sample(anti_preferences['genres_to_include'], min(2, len(anti_preferences['genres_to_include'])))
            params.update({
                'with_genres': '|'.join(map(str, genres_to_use)),
                'primary_release_date.gte': f"{anti_preferences['min_year']}-01-01",
                'primary_release_date.lte': f"{anti_preferences['max_year']}-12-31",
                'vote_average.lte': min(5.0, anti_preferences.get('vote_average_lte', 5.0)),
                'sort_by': anti_preferences.get('sort_preference', 'vote_average.asc')
            })

        # Attempt initial request with anti-preferences
        logger.info(f"Fetching worst-rated movies with params: {params}")
        
        response = requests.get(url, headers=get_tmdb_headers(), params=params, timeout=10)
        response.raise_for_status()
        movies_data = response.json().get('results', [])

        # Check if we got results, otherwise switch to fallback
        if not movies_data:
            logger.warning("No valid results found for anti-preferences. Using fallback parameters for low-rated movies.")
            params = {
                'language': 'en-US',
                'include_adult': False,
                'vote_count.gte': 50,
                'vote_average.lte': 3.5,   # Target very low-rated movies
                'sort_by': 'vote_average.asc',
                'page': random.randint(1, 5)
            }
            response = requests.get(url, headers=get_tmdb_headers(), params=params, timeout=10)
            response.raise_for_status()
            movies_data = response.json().get('results', [])

        # Shuffle and limit to requested count
        random.shuffle(movies_data)
        movies_data = movies_data[:count]

        # Gather valid posters only
        posters = [
            {
                'id': movie['id'],
                'title': movie.get('title', 'Unknown Title'),
                'poster_url': f"{TMDB_IMAGE_BASE_URL}{movie['poster_path']}",
                'year': movie.get('release_date', '')[:4],
                'genre_ids': movie.get('genre_ids', []),
                'summary': movie.get('overview', 'No summary available'),
                'vote_average': movie.get('vote_average', 0)
            }
            for movie in movies_data if movie.get('poster_path')
        ]

        logger.info(f"Final number of posters with valid images: {len(posters)}")
        
        return posters
        
    except Exception as e:
        logger.error(f"Error fetching worst rated movies: {str(e)}")
        return []  # Return an empty list in case of error

def analyze_taste(selected_movies):
    """Analyze user's taste and generate description of what they'd hate"""
    try:
        movie_details = get_movie_details(selected_movies)
        
        prompt = f"""Based on these selected movies:
{json.dumps(movie_details, indent=2)}

Create a JSON object with two sections:
1. "taste_profile": A brief, engaging description of what this person loves in movies (tone, genres, themes they gravitate toward)
2. "anti_preferences": A fun, dramatic description of what movies would be their worst nightmare

Make it entertaining but insightful. Keep each description under 50 words.

Return as JSON with these two fields only."""

        truncated_prompt = _truncate_text(prompt)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a witty movie critic who specializes in analyzing viewer preferences."},
                {"role": "user", "content": truncated_prompt}
            ],
            response_format={ "type": "json_object" }
        )
        
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        logger.error(f"Error analyzing taste: {str(e)}")
        return {
            "taste_profile": "A lover of high-quality, engaging cinema with refined taste.",
            "anti_preferences": "Would probably run screaming from low-budget disasters and poorly executed films."
        }
    
def _truncate_text(text, max_chars=4000):
    """Truncate text to max chars while keeping JSON valid"""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    # Try to find last complete object by finding last '}'
    last_brace = truncated.rfind('}')
    if last_brace != -1:
        return truncated[:last_brace + 1]
    return truncated