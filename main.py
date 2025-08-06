'''
This is a Flask web application that allows users to submit their CPS (Clicks Per Second) scores and view
a leaderboard. The application stores the scores in a JSON file and generates a graph of the top 10 scores
using Matplotlib. The leaderboard is displayed on the main page, and users can submit their scores and
names through AJAX requests. The application also includes routes for rendering templates and serving
static files.

Coded by: Aryan Vyahalkar, Arav Vyahalkar, Tristan Owen, Nour El-Sadek
'''

# Import required librarie
from flask import Flask, render_template, request, jsonify, send_from_directory
import json
import os
import matplotlib.pyplot as plt

# Creates Flask object
app = Flask(__name__)

# Creates score/scoreboard file that is a json
SCORES_FILE = 'scores.json'
GRAPH_PATH = 'static/scoreboard.png'

# loads scores from score file 
def load_scores():
    if not os.path.exists(SCORES_FILE):
        return []
    with open(SCORES_FILE, 'r') as f:
        return json.load(f)

# saves new scores into score json
def save_scores(scores):
    with open(SCORES_FILE, 'w') as f:
        json.dump(scores, f)

# updates leader board by loading and saving scores using above functions
def update_leaderboard(cps, name="Anonymous"):
    scores = load_scores()
    scores.append({"cps": round(cps, 3), "name": name})
    scores = sorted(scores, key=lambda x: x['cps'], reverse=True)[:10]
    save_scores(scores)
    return scores

# Generate a line graph of the top 10 scores 
def generate_graph(scores):

    # Sort scores descending and reverse to plot left-to-right
    scores_sorted = sorted(scores, key=lambda x: x['cps'], reverse=True)[:10]
    scores_sorted = list(reversed(scores_sorted))  # so the best is at the right
    x = list(range(1, len(scores_sorted) + 1))
    y = [s['cps'] for s in scores_sorted]
    labels = [f"{s['cps']} - {s['name']}" for s in scores_sorted]

    # Set up the graph style
    plt.figure(figsize=(8, 4))
    plt.plot(x, y, marker='o', linestyle='-', color='deepskyblue', linewidth=2, markerfacecolor='blue')

    # Label each point on the graph
    for i, txt in enumerate(labels):
        plt.text(x[i], y[i], txt, ha='center', va='bottom', fontsize=8)

    # Axi titles and grid
    plt.title("Top 10 CPS Scores")
    plt.xlabel("Rank")
    plt.ylabel("CPS")
    plt.xticks(x)
    plt.grid(True, linestyle='--', alpha=0.5)

    # Save the figure to static folder
    plt.tight_layout()
    plt.savefig(GRAPH_PATH)
    plt.close()

# defines a route that creates a render_template using load scores function
@app.route('/')
def index():
    leaderboard = load_scores()
    return render_template('index.html', leaderboard=leaderboard)

# creates a route that returns a render_template for a scoreboard by loading scores and making a graph
@app.route('/scoreboard')
def scoreboard():
    leaderboard = load_scores()
    generate_graph(leaderboard)
    return render_template('scoreboard.html')

# makes a route that saves new scores to the top 10 leaderboard by saving in the json and leaderboard 
@app.route('/submit_score', methods=['POST'])
def submit_score():
    data = request.json
    cps = round(data.get('cps', 0), 3)
    leaderboard = update_leaderboard(cps)

    # Check if score is in the top 10 (to show name input)
    is_top_10 = any(score['cps'] == cps for score in leaderboard)
    return jsonify({'top10': is_top_10})

# defines a route that allows a name to be associated with the score 
@app.route('/submit_name', methods=['POST'])
def submit_name():
    data = request.json
    name = data.get('name', 'Anonymous')
    cps = round(data.get('cps', 0), 3)

    scores = load_scores()
    for score in scores:
        # Only update name if score is anonymous and matches submitted CPS
        if score['cps'] == cps and score['name'] == "Anonymous":
            score['name'] = name
            break
    save_scores(scores)
    return jsonify({'success': True})

# makes file only run if it is the main file being run
if __name__ == '__main__':
    app.run(debug=True)