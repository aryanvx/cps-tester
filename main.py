'''
This is a Flask web application that allows users to submit their CPS (Clicks Per Second) scores and view
a leaderboard. The application stores the scores in PostgreSQL and generates a graph of the top 10 scores
using Matplotlib served dynamically.

Coded by: Aryan Vyahalkar, Arav Vyahalkar, Tristan Owen, & Nour El-Sadek
Modified for Render deployment with PostgreSQL
'''

# Import required libraries
from flask import Flask, render_template, request, jsonify, send_file
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import io

# Creates Flask object
app = Flask(__name__)

# Database connection string from environment variable
DATABASE_URL = os.environ.get('DATABASE_URL')

# Get database connection
def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

# Initialize database table
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS scores (
            id SERIAL PRIMARY KEY,
            cps DECIMAL(10, 3) NOT NULL,
            name VARCHAR(100) DEFAULT 'Anonymous',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

# Load top 10 scores from database
def load_scores():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT cps, name FROM scores ORDER BY cps DESC LIMIT 10')
    scores = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(score) for score in scores]

# Add a new score to database
def add_score(cps, name="Anonymous"):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO scores (cps, name) VALUES (%s, %s) RETURNING id', (cps, name))
    score_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return score_id

# Update score name by ID
def update_score_name(score_id, name):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('UPDATE scores SET name = %s WHERE id = %s', (name, score_id))
    conn.commit()
    cur.close()
    conn.close()

# Check if a score makes top 10
def is_top_10(cps):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM (SELECT cps FROM scores ORDER BY cps DESC LIMIT 10) AS top10 WHERE cps <= %s', (cps,))
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count > 0

# Generate a line graph of the top 10 scores in memory
def generate_graph(scores):
    # Sort scores descending and reverse to plot left-to-right
    scores_sorted = sorted(scores, key=lambda x: x['cps'], reverse=True)[:10]
    scores_sorted = list(reversed(scores_sorted))  # so the best is at the right
    x = list(range(1, len(scores_sorted) + 1))
    y = [float(s['cps']) for s in scores_sorted]
    labels = [f"{s['cps']} - {s['name']}" for s in scores_sorted]

    # Set up the graph style
    plt.figure(figsize=(8, 4))
    plt.plot(x, y, marker='o', linestyle='-', color='deepskyblue', linewidth=2, markerfacecolor='blue')

    # Label each point on the graph
    for i, txt in enumerate(labels):
        plt.text(x[i], y[i], txt, ha='center', va='bottom', fontsize=8)

    # Axis titles and grid
    plt.title("Top 10 CPS Scores")
    plt.xlabel("Rank")
    plt.ylabel("CPS")
    plt.xticks(x)
    plt.grid(True, linestyle='--', alpha=0.5)

    # Save the figure to BytesIO buffer instead of file
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf

# Home page route
@app.route('/')
def index():
    leaderboard = load_scores()
    return render_template('index.html', leaderboard=leaderboard)

# Scoreboard page route
@app.route('/scoreboard')
def scoreboard():
    return render_template('scoreboard.html')

# Serve scoreboard graph dynamically
@app.route('/scoreboard.png')
def scoreboard_graph():
    leaderboard = load_scores()
    buf = generate_graph(leaderboard)
    return send_file(buf, mimetype='image/png')

# Submit score endpoint
@app.route('/submit_score', methods=['POST'])
def submit_score():
    data = request.json
    cps = round(data.get('cps', 0), 3)
    
    # Add score to database and get ID
    score_id = add_score(cps)
    
    # Check if score is in top 10
    top10 = is_top_10(cps)
    
    return jsonify({'top10': top10, 'score_id': score_id})

# Submit name endpoint
@app.route('/submit_name', methods=['POST'])
def submit_name():
    data = request.json
    name = data.get('name', 'Anonymous')
    score_id = data.get('score_id')
    
    if score_id:
        update_score_name(score_id, name)
    
    return jsonify({'success': True})

# Initialize database on first run
if __name__ == '__main__':
    init_db()
    app.run(debug=True)