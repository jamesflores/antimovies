# Movie Anti-Matcher

Demo: https://movies.jamesf.xyz

Video: https://youtu.be/5jbmsSQj9jw

Movie Anti-Matcher is a Flask web application that allows users to discover movies they’d likely dislike based on movies they select as "liking". The app uses OpenAI gpt-4o-mini to provide taste analysis and preferences.
You will be returned an infinitely scrolling list of movies that align with “anti-preferences” by constrasting the themes, genres, and ratings of the user’s selected movies. 
This project was my capstone for Harvard's CS50x. It builds on the Flask knowledge we gained in week 9 and the movie themes presented in week 7 SQL psets.
Streaming platforms already do a great job of suggesting movies we might like to watch, I just inverted this idea and presented movies you wouldn't like to watch!

## Project Structure

### Overview

The Movie Anti-Matcher application was designed with Flask for the backend and HTML, CSS, and JavaScript on the frontend, with by HTMX for dynamic interactions. It leverages the free TMDb (The Movie Database) API for fetching movie data, images, and ratings.
OpenAI gpt-4o-mini is used to analyze the user’s taste and generate “anti-preferences.”

Example:

**What You Love**
`This viewer craves heart-pounding action and mind-bending sci-fi, delighting in epic adventures where heroes battle formidable foes. They thrive on thrilling narratives that keep them on the edge of their seats, particularly those that weave in a touch of horror or the macabre.`

**Your Anti-Matches**
`Imagine a world where nothing happens—no explosions, no heroes, just a lengthy dialogue about the price of tea in China. Movies drenched in relentless melodrama or existential musings would be their personal purgatory, eliciting yawns instead of thrills. Yikes!`


### Project Files

1.	app.py
- Main application file for Flask
- Contains routes to handle requests and interact with the third-party APIs
- Primary route `/get-recommendations` takes the user's movie inputs
- Uses sessions to store selections and anti-preferences
- Serves recommendations by requiring `movie_service.py`
- Error pages are served if the third-party APIs are not working

2.	movie_service.py:
- Handles all third-party API calls to TMDb and OpenAI
- get_random_posters: returns a random set of popular movies to initially display
- get_contrasting_movies: returns movie recommendations by flipping the user’s preferences. Returns a broader selection of low-rated movies if none are found
- analyze_preferences and analyze_taste: OpenAI wrappers to analyze user-selected movies and generate JSON objects that contain anti-preferences, defining genres, years, and ratings for undesirable movies

3.  config.py:
- Handles setting and configuration of environment variables
- Note: set SECRET_KEY (optional), TMDB_API_KEY and OPENAI_API_KEY in your environment (.env file works locally)

4.	Templates
- poster_grid.html: renders the Bootsrap grid of movies, displaying movie posters and an overlay of basic information
- base.html: contains shared layout components, primarily for the footer
- index.html: the main page that houses all the components for this single page app

5.	static/css/custom.css
- Custom CSS file. Includes themes for standard and anti-match modes, so the user knows when they are selecting movies to like and browsing anti-movies.

6.	static/js/movie.js
- Dynamic functionality to handle the “Find My Anti-Movies” button
- Allow infinite scrolling to load more movie posters
- Manages selection states and overlay when processing

### Challenges and Future Enhancements

1. Performance
Initial development faced latency issues due to multiple API calls.

2. Error and Fallback Handling
If OpenAI credits ran out, an invalid response was returned or no matches were returned from anti-preferences, the app returned no results.
Implementing a set of broader parameters to fetch a “fallback” set resolved this, including resorting to worst rated movies.

3. User Profiles
Add ability to introduce user accounts to save selections, allowing users to save "liked" movies and anti-movies (if they really wanted too!).

## Acknowledgements

Thanks to David Malan and the CS50 staff for providing this educational resource for everyone across the world. After completing CS50p and CS50w I questioned whether I would even bother attempting CS50x.
I couldn't help myself and decided to tackle the challenge in 2024. Coming from a Computer Science background in the early 2000s (I'm showing my age!), it was great to revisit the concepts
presented in CS50x again. I also have to thank the CS50.ai Duck for some useful tips during the problem sets. This project was enhanced and amplified by ChatGPT, Claude and GitHub's Copilot.