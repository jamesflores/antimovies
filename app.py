import logging
from flask import Flask, render_template, jsonify, request, session
from movie_service import get_random_posters, get_worst_rated_movies, analyze_preferences, analyze_taste
from config import SECRET_KEY
import math

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = SECRET_KEY

def calculate_movies_needed():
    """Calculate number of movies needed based on default card size"""
    # Using Bootstrap's default breakpoints and our card size (col-md-3 = 4 cards per row)
    # Assuming each card is roughly 400px tall (300px image + 100px content)
    viewport_height = int(request.headers.get('Viewport-Height', 800))  # Default to 800 if not provided
    viewport_width = int(request.headers.get('Viewport-Width', 1200))  # Default to 1200 if not provided
    
    cards_per_row = 4  # Based on col-md-3
    if viewport_width < 768:  # Bootstrap's md breakpoint
        cards_per_row = 2
    
    card_height = 400  # Approximate height of each card
    rows_needed = math.ceil(viewport_height / card_height)
    
    # Calculate total cards needed plus one extra row
    total_cards = (rows_needed + 1) * cards_per_row
    
    # Round up to nearest 5 for cleaner numbers
    return math.ceil(total_cards / 5) * 5

@app.route('/')
def index():
    try:
        movies_needed = calculate_movies_needed()
        initial_posters = get_random_posters(count=movies_needed)
        return render_template('index.html', posters=initial_posters, is_recommendation=False)
    except Exception as e:
        logger.error(f"Error loading initial posters: {str(e)}")
        return render_template('error.html', message="Unable to load posters. Please try again later.")

@app.route('/load-more-posters')
def load_more_posters():
    movies_needed = calculate_movies_needed()
    posters = get_random_posters(count=movies_needed)
    return render_template('poster_grid.html', posters=posters)

@app.route('/get-recommendations', methods=['POST'])
def get_recommendations():
    try:
        selected_movies = request.form.getlist('selected-movies')
        logger.info(f"Selected movies: {selected_movies}")
        
        movies_needed = calculate_movies_needed()
        anti_preferences = analyze_preferences(selected_movies)
        taste_analysis = analyze_taste(selected_movies)
        
        session['anti_preferences'] = anti_preferences
        session['taste_analysis'] = taste_analysis
        
        # Attempt to get AI-based recommendations
        anti_recommendations = get_worst_rated_movies(count=movies_needed, anti_preferences=anti_preferences)

        # Fallback to generic low-rated movies if no AI-based recommendations are found
        if not anti_recommendations:
            logger.warning("No AI-based recommendations found, using generic low-rated movies.")
            anti_recommendations = get_worst_rated_movies(count=movies_needed)

        return render_template('poster_grid.html', 
                               posters=anti_recommendations,
                               is_recommendation=True,
                               taste_analysis=taste_analysis)
    except Exception as e:
        logger.error(f"Critical error in get_recommendations: {str(e)}")
        return "An error occurred while trying to load recommendations. Please try again later.", 500

@app.route('/load-more-anti-recommendations')
def load_more_anti_recommendations():
    movies_needed = calculate_movies_needed()
    anti_preferences = session.get('anti_preferences')
    
    posters = get_worst_rated_movies(
        count=movies_needed,
        anti_preferences=anti_preferences
    )
    
    return render_template('poster_grid.html', 
                         posters=posters,
                         is_recommendation=True)

@app.route('/refresh-posters')
def refresh_posters():
    """Handle the restart functionality"""
    try:
        session.clear()
        
        movies_needed = calculate_movies_needed()
        initial_posters = get_random_posters(count=movies_needed)
        return render_template('poster_grid.html', posters=initial_posters)
    except Exception as e:
        logger.error(f"Error refreshing posters: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/reset-session', methods=['POST'])
def reset_session():
    """Reset the session and all state"""
    try:
        session.clear()
        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"Error resetting session: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)