# HTML and CSS interface (all at the top of the file)
HTML_CODE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Team OPR Analysis</title>
  <link href="https://fonts.googleapis.com/css?family=Poppins:400,600&display=swap" rel="stylesheet">
  <style>
    /* Animated Gradient Background */
    body {
      margin: 0;
      padding: 0;
      font-family: 'Poppins', sans-serif;
      background: linear-gradient(45deg, #861f18, #f0a202, #861f18, #f0a202);
      background-size: 400% 400%;
      animation: gradientShift 16s ease infinite;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      overflow: hidden;
    }
    @keyframes gradientShift {
      0% { background-position: 0% 50%; }
      50% { background-position: 100% 50%; }
      100% { background-position: 0% 50%; }
    }
    
    /* Container with glassmorphism and animated rotating overlay */
    .container {
      position: relative;
      width: 90%;
      max-width: 600px;
      background: rgba(255, 255, 255, 0.1);
      padding: 30px;
      border-radius: 15px;
      backdrop-filter: blur(10px);
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.37);
      text-align: center;
      overflow: hidden;
      animation: fadeIn 1s ease-in-out;
    }
    .container::before {
      content: "";
      position: absolute;
      top: -50%;
      left: -50%;
      width: 200%;
      height: 200%;
      background: conic-gradient(from 0deg, transparent, rgba(255,255,255,0.2), transparent, transparent);
      animation: rotateBG 6s linear infinite;
      pointer-events: none;
      z-index: 0;
    }
    .container > * {
      position: relative;
      z-index: 1;
    }
    @keyframes rotateBG {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: scale(0.9); }
      to { opacity: 1; transform: scale(1); }
    }
    
    /* Neon styled header */
    h1 {
      font-size: 2rem;
      margin-bottom: 20px;
      text-shadow: 0 0 5px #fff, 0 0 10px #f0a202, 0 0 20px #f0a202, 0 0 40px #f0a202;
    }
    
    /* Styled form elements with custom file input */
    form input[type="file"],
    form input[type="text"] {
      width: 100%;
      padding: 12px 15px;
      margin: 10px 0;
      border: 2px solid rgba(255,255,255,0.4);
      border-radius: 8px;
      background: rgba(255,255,255,0.1);
      color: white;
      font-size: 1rem;
      transition: border 0.3s, box-shadow 0.3s;
    }
    form input[type="file"]::file-selector-button {
      border: none;
      padding: 10px 20px;
      margin-right: 10px;
      border-radius: 5px;
      background: #f0a202;
      color: #861f18;
      cursor: pointer;
      transition: background 0.3s;
    }
    form input[type="file"]::file-selector-button:hover {
      background: #861f18;
      color: white;
    }
    form input[type="text"]:focus,
    form input[type="file"]:focus {
      outline: none;
      border-color: #f0a202;
      box-shadow: 0 0 10px rgba(240, 162, 2, 0.6);
    }
    button {
      width: 100%;
      padding: 12px 15px;
      margin: 15px 0;
      border: none;
      border-radius: 8px;
      background: #f0a202;
      color: #861f18;
      font-size: 1.1rem;
      font-weight: bold;
      cursor: pointer;
      transition: transform 0.3s, background 0.3s;
    }
    button:hover {
      background: #861f18;
      color: white;
      transform: scale(1.05);
    }
    
    /* Output and spinner styles */
    pre {
      background: rgba(255, 255, 255, 0.15);
      padding: 20px;
      text-align: left;
      border-radius: 10px;
      max-height: 250px;
      overflow-y: auto;
      color: white;
      margin-top: 20px;
      font-family: 'Courier New', monospace;
      font-size: 0.9rem;
    }
    .spinner {
      border: 6px solid rgba(255,255,255,0.3);
      border-top: 6px solid #f0a202;
      border-radius: 50%;
      width: 50px;
      height: 50px;
      animation: spin 1s linear infinite;
      margin: 20px auto;
      display: none;
    }
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>🚀 super amazing awesome curiosity scouting poo poo</h1>
    <form id="oprForm" method="POST" enctype="multipart/form-data">
      <input type="file" id="csvFile" name="csvFile" accept=".csv" required>
      <input type="text" id="myTeam" name="myTeam" placeholder="Enter your team number (e.g., 11770.0)" required>
      <button type="submit">Analyze</button>
    </form>
    <div class="spinner" id="spinner"></div>
    <pre id="output">Awaiting analysis...</pre>
  </div>
  <script>
    const form = document.getElementById("oprForm");
    const spinner = document.getElementById("spinner");
    const output = document.getElementById("output");
    
    form.addEventListener("submit", function(e) {
      e.preventDefault();
      output.style.display = "none";
      spinner.style.display = "block";
      const formData = new FormData(this);
      fetch("/analyze", { method: "POST", body: formData })
        .then(response => response.text())
        .then(data => {
          spinner.style.display = "none";
          output.style.display = "block";
          output.innerText = data;
        })
        .catch(error => {
          spinner.style.display = "none";
          output.style.display = "block";
          output.innerText = "Error: " + error;
        });
    });
  </script>
</body>
</html>

"""

# The rest of the file is the Python code running a Flask app that uses your analysis.

from flask import Flask, request
import pandas as pd
from itertools import combinations

app = Flask(__name__)

@app.route('/')
def index():
    return HTML_CODE

@app.route('/analyze', methods=['POST'])
def analyze():
    # Get the uploaded CSV file
    file = request.files.get("csvFile")
    if not file:
        return "No file uploaded.", 400
    try:
        # Note: header=1 because the first row is extra, and row 1 contains the proper headers.
        df = pd.read_csv(file, header=1)
    except Exception as e:
        return f"Error reading CSV file: {e}", 400

    # Clean up column names
    df.columns = df.columns.str.strip()
    
    # Define column names as used in your CSV
    team_col = "Team #"
    sample_opr_col = "Observed SAMPLEOPR"
    specimen_opr_col = "Observed SPECIMEN OPR"
    
    # Convert OPR columns to numeric and fill NaN with 0
    df[sample_opr_col] = pd.to_numeric(df[sample_opr_col], errors='coerce').fillna(0)
    df[specimen_opr_col] = pd.to_numeric(df[specimen_opr_col], errors='coerce').fillna(0)
    
    # Create the 'Best OPR' column
    df["Best OPR"] = df[[sample_opr_col, specimen_opr_col]].max(axis=1)
    
    # Ensure team numbers are strings and stripped of extra spaces
    df[team_col] = df[team_col].astype(str).str.strip()
    teams_dict = dict(zip(df[team_col], df["Best OPR"]))
    
    # Generate all possible two-team combinations
    all_pairs = list(combinations(teams_dict.keys(), 2))
    pair_scores = [(t1, t2, teams_dict[t1] + teams_dict[t2]) for t1, t2 in all_pairs]
    pair_scores.sort(key=lambda x: x[2], reverse=True)
    
    # Prepare the output as a list of lines
    output_lines = []
    output_lines.append("Top 10 Team Combinations by Combined OPR:")
    for i, (team1, team2, combined) in enumerate(pair_scores[:10], start=1):
        output_lines.append(f"{i}. Teams {team1} & {team2} => {combined:.2f}")
    
    # Get team number from the form
    my_team = request.form.get("myTeam", "11770").strip()
    if my_team in teams_dict:
        # Determine best partner for the given team
        partners = []
        for t in teams_dict:
            if t == my_team:
                continue
            combined_opr = teams_dict[my_team] + teams_dict[t]
            partners.append((t, combined_opr))
        partners.sort(key=lambda x: x[1], reverse=True)
        
        output_lines.append(f"\nBest Partners for Team {my_team}:")
        for i, (t, c) in enumerate(partners[:12], start=1):
            output_lines.append(f"{i}. Team {t} => {c:.2f}")
        
        # Get ranking for the pairing of my_team with its best partner
        best_partner = partners[0][0] if partners else None
        rank = get_team_pair_rank(my_team, pair_scores, teams_dict)
        if rank is not None:
            output_lines.append(f"\nThe pairing of team {my_team} with its best partner (Team {best_partner}) is ranked #{rank} in combined OPR.")
        else:
            output_lines.append(f"\nTeam {my_team} not found in the data.")
    else:
        output_lines.append(f"\nTeam {my_team} not found in the data.")
    
    # Competitiveness check of the top pair
    if is_top_pair_unbeatable(pair_scores):
        output_lines.append("The top team combination is unbeatable.")
    else:
        output_lines.append("Another team combination can beat the top pair.")
    
    # Return the output as plain text
    return "\n".join(output_lines)

def is_top_pair_unbeatable(pair_scores):
    """
    Returns True if the top pair (first element in the sorted list) has a combined OPR
    that no other pair matches or exceeds.
    """
    if not pair_scores:
        return False
    best_score = pair_scores[0][2]
    if len(pair_scores) == 1:
        return True
    return all(score < best_score for _, _, score in pair_scores[1:])

def get_team_pair_rank(my_team, pair_scores, teams_dict):
    """
    Returns the 1-indexed rank of the pairing of my_team with its best partner among all combinations.
    """
    if my_team not in teams_dict:
        return None

    best_partner = None
    best_score = -float('inf')
    for team, opr in teams_dict.items():
        if team == my_team:
            continue
        combined = teams_dict[my_team] + opr
        if combined > best_score:
            best_score = combined
            best_partner = team

    for rank, (t1, t2, score) in enumerate(pair_scores, start=1):
        if {t1, t2} == {my_team, best_partner}:
            return rank
    return None

if __name__ == '__main__':
    app.run(debug=True)
