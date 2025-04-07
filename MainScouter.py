from flask import Flask, request, session
import pandas as pd
from itertools import combinations
import io

app = Flask(__name__)
app.secret_key = "CHANGE_ME_TO_SOMETHING_RANDOM"  # Replace with a secure key for production

HTML_CODE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Team OPR Analysis</title>
  <style>
    body { 
      font-family: Arial, sans-serif; 
      margin: 20px; 
      background-color: #861f18;
    }
    .container { 
      max-width: 1200px; 
      margin: auto; 
      background: #fff; 
      padding: 20px; 
      border-radius: 5px; 
      box-shadow: 0 0 10px rgba(0,0,0,0.1); 
    }
    label {
      font-weight: bold;
    }
    input[type="text"], input[type="file"], select { 
      width: 100%; 
      padding: 8px; 
      margin: 5px 0 15px 0; 
      box-sizing: border-box; 
      border: 1px solid #861f18;
      border-radius: 3px;
    }
    button { 
      padding: 10px 20px; 
      background-color: #f0a202; 
      border: none; 
      color: white; 
      border-radius: 3px; 
      cursor: pointer; 
      margin-top: 5px;
    }
    button:hover { 
      background-color: #861f18; 
    }
    .output-container {
      display: flex;
      justify-content: space-between;
      flex-wrap: wrap;
      margin-top: 20px;
    }
    .output-box {
      flex: 1 1 30%;
      border: 2px solid #861f18;
      padding: 15px;
      margin: 10px;
      border-radius: 5px;
      background-color: #f9f9f9;
      min-width: 280px;
    }
    .output-box h2 {
      margin-top: 0;
      font-size: 1.2em;
      border-bottom: 1px solid #861f18;
      padding-bottom: 5px;
    }
    .dropdown-container {
      margin-bottom: 15px;
    }
    select[multiple] {
      height: 100px;
    }
    /* Style for removed teams */
    option.removed {
      text-decoration: line-through;
      color: #888;
    }
    .instructions {
      font-size: 0.9em;
      color: #555;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>Team OPR Analysis</h1>
    <!-- Single form for CSV upload and reanalysis -->
    <form id="oprForm" method="POST" enctype="multipart/form-data">
      <div>
        <label for="csvFile">Upload CSV file (only needed first time):</label>
        <input type="file" id="csvFile" name="csvFile" accept=".csv">
      </div>
      <div>
        <label for="myTeam">Enter your team number (include .0 if applicable):</label>
        <input type="text" id="myTeam" name="myTeam" value="11770" required>
      </div>
      
      <div class="dropdown-container">
        <label for="removeTeam">Select teams to eliminate from pairing:</label>
        <span class="instructions">(Hold Ctrl/Cmd to select multiple teams)</span>
        <!-- Dropdown will be populated dynamically -->
        <select id="removeTeam" name="removeTeam" multiple>
        </select>
      </div>
      
      <button type="submit">Run Analysis</button>
    </form>
    
    <div id="resultContainer" class="output-container"></div>
  </div>
  
  <script>
    // Note: We removed the auto-submit on dropdown change.
    // Now you can select multiple teams and then click "Run Analysis" to remove them.
    
    // Populate the removal dropdown with all teams and mark removed teams as selected and with a strikethrough.
    function populateDropdown(teams, removedTeams) {
      const removeSelect = document.getElementById('removeTeam');
      removeSelect.innerHTML = ""; // Clear existing options

      teams.forEach(team => {
        const opt = document.createElement("option");
        opt.value = team;
        opt.textContent = team;
        // If this team is already removed, mark it as selected and add a visual strike-through.
        if (removedTeams.includes(team)) {
          opt.selected = true;
          opt.classList.add("removed");
        }
        removeSelect.appendChild(opt);
      });
    }

    // Intercept form submission and update the page with JSON response.
    document.getElementById("oprForm").addEventListener("submit", function(e) {
      e.preventDefault();
      const formData = new FormData(document.getElementById("oprForm"));
      fetch("/analyze", { method: "POST", body: formData })
        .then(response => response.json())
        .then(data => {
          document.getElementById("resultContainer").innerHTML = data.resultHTML;
          populateDropdown(data.teams, data.removedTeams);
        })
        .catch(err => {
          document.getElementById("resultContainer").innerHTML = "<p>Error: " + err + "</p>";
        });
    });
  </script>
</body>
</html>
"""

@app.route('/')
def index():
    return HTML_CODE

@app.route('/analyze', methods=['POST'])
def analyze():
    """
    1) If a new CSV file is uploaded, parse it and store its text in session.
    2) Otherwise, retrieve the CSV data from session.
    3) Read the 'myTeam' input (and store it in session).
    4) Persist a removal list in session; any teams submitted for removal are added permanently.
    5) Remove those teams from pairing calculations.
    6) Return JSON with the analysis result HTML, full list of teams, and removed teams.
    """
    # 1) CSV file upload handling.
    file = request.files.get("csvFile")
    if file and file.filename:
        try:
            df = pd.read_csv(file, header=1)
        except Exception as e:
            return {"resultHTML": f"<p>Error reading CSV: {e}</p>", "teams": [], "removedTeams": []}
        session["csv_data"] = df.to_csv(index=False)
        # Initialize removal list when a new CSV is uploaded.
        session["removed_teams"] = []
    else:
        if "csv_data" not in session:
            return {
                "resultHTML": "<p>No CSV data found. Please upload a CSV first.</p>",
                "teams": [],
                "removedTeams": []
            }
        csv_text = session["csv_data"]
        df = pd.read_csv(io.StringIO(csv_text))
    
    # 2) Clean up column names.
    df.columns = df.columns.str.strip()
    
    # 3) Get the user's team from the form (or session).
    my_team = request.form.get("myTeam", "").strip()
    if my_team:
        session["my_team"] = my_team
    else:
        my_team = session.get("my_team", "")
    
    # 4) Persist removed teams in session.
    current_removed = session.get("removed_teams", [])
    # Get removal selections from form (this can be multiple teams).
    new_removed = request.form.getlist("removeTeam")
    # Once a team is removed, it stays removed.
    for t in new_removed:
        if t not in current_removed:
            current_removed.append(t)
    session["removed_teams"] = current_removed

    # Define CSV column names.
    team_col = "Team #"
    sample_opr_col = "Observed SAMPLEOPR"
    specimen_opr_col = "Observed SPECIMEN OPR"
    
    # 5) Convert OPR columns to numeric.
    df[sample_opr_col] = pd.to_numeric(df[sample_opr_col], errors='coerce').fillna(0)
    df[specimen_opr_col] = pd.to_numeric(df[specimen_opr_col], errors='coerce').fillna(0)
    
    # Build a dictionary of teams from CSV.
    teams_dict = {}
    for _, row in df.iterrows():
        team_str = str(row[team_col]).strip()
        teams_dict[team_str] = {
            "sample": row[sample_opr_col],
            "specimen": row[specimen_opr_col]
        }
    
    # Remove all teams in the persistent removal list.
    removal_message = ""
    for t in current_removed:
        if t in teams_dict:
            del teams_dict[t]
            removal_message += f"Removed team <del>{t}</del> from pairing calculations.<br>"
        else:
            removal_message += f"Team {t} not found, so not removed.<br>"

    # 6) Generate all possible two-team pairings.
    pair_details = []
    for team1, team2 in combinations(teams_dict.keys(), 2):
        s1 = teams_dict[team1]["sample"]
        p1 = teams_dict[team1]["specimen"]
        s2 = teams_dict[team2]["sample"]
        p2 = teams_dict[team2]["specimen"]

        optionA = s1 + p2
        optionB = p1 + s2
        if optionA >= optionB:
            best_score = optionA
            team1_role = "SAMPLE"
            team2_role = "SPECIMEN"
        else:
            best_score = optionB
            team1_role = "SPECIMEN"
            team2_role = "SAMPLE"
        pair_details.append((team1, team2, team1_role, team2_role, best_score, optionA, optionB))
    
    pair_details.sort(key=lambda x: x[4], reverse=True)
    
    # Build HTML output (three output boxes).
    result_html = ""
    # Box 1: Overall Top Pair Combinations.
    result_html += "<div class='output-box'>"
    if removal_message:
        result_html += f"<p>{removal_message}</p>"
    result_html += "<h2>Overall Top Pair Combinations</h2>"
    if pair_details:
        result_html += "<ul>"
        for i, (t1, t2, r1, r2, score, optA, optB) in enumerate(pair_details[:10], start=1):
            result_html += (
                f"<li>{i}. {t1} ({r1}) &amp; {t2} ({r2}) => Combined OPR: {score:.2f} "
                f"(Option A: {optA:.2f}, Option B: {optB:.2f})</li>"
            )
        result_html += "</ul>"
    else:
        result_html += "<p>No pairings found.</p>"
    result_html += "</div>"
    
    # Box 2: Top Pairings Including Your Team.
    if my_team in teams_dict:
        my_team_pairs = [pd for pd in pair_details if my_team in (pd[0], pd[1])]
        result_html += "<div class='output-box'>"
        result_html += f"<h2>Top Pairings with Team {my_team}</h2>"
        if my_team_pairs:
            result_html += "<ul>"
            for i, (t1, t2, r1, r2, score, optA, optB) in enumerate(my_team_pairs[:10], start=1):
                result_html += (
                    f"<li>{i}. {t1} ({r1}) &amp; {t2} ({r2}) => Combined OPR: {score:.2f} "
                    f"(Option A: {optA:.2f}, Option B: {optB:.2f})</li>"
                )
            result_html += "</ul>"
        else:
            result_html += f"<p>No pairings available with team {my_team}.</p>"
        result_html += "</div>"
        
        # Box 3: Analysis & Recommendation for Your Team.
        result_html += "<div class='output-box'>"
        result_html += f"<h2>Analysis & Recommendation for Team {my_team}</h2>"
        # Best partner if playing as SAMPLE.
        best_sample_partner = None
        best_sample_score = -float('inf')
        best_sample_details = ""
        for other in teams_dict:
            if other == my_team:
                continue
            cur_score = teams_dict[my_team]["sample"] + teams_dict[other]["specimen"]
            if cur_score > best_sample_score:
                best_sample_score = cur_score
                best_sample_partner = other
                best_sample_details = (
                    f"{my_team} as SAMPLE ({teams_dict[my_team]['sample']}) + "
                    f"{other} as SPECIMEN ({teams_dict[other]['specimen']})"
                )
        # Best partner if playing as SPECIMEN.
        best_specimen_partner = None
        best_specimen_score = -float('inf')
        best_specimen_details = ""
        for other in teams_dict:
            if other == my_team:
                continue
            cur_score = teams_dict[my_team]["specimen"] + teams_dict[other]["sample"]
            if cur_score > best_specimen_score:
                best_specimen_score = cur_score
                best_specimen_partner = other
                best_specimen_details = (
                    f"{my_team} as SPECIMEN ({teams_dict[my_team]['specimen']}) + "
                    f"{other} as SAMPLE ({teams_dict[other]['sample']})"
                )
        result_html += (
            f"<p>Best partner if playing as SAMPLE: Team {best_sample_partner} => OPR {best_sample_score:.2f}<br>"
            f"Details: {best_sample_details}</p>"
        )
        result_html += (
            f"<p>Best partner if playing as SPECIMEN: Team {best_specimen_partner} => OPR {best_specimen_score:.2f}<br>"
            f"Details: {best_specimen_details}</p>"
        )
        s_val = teams_dict[my_team]["sample"]
        p_val = teams_dict[my_team]["specimen"]
        if s_val > p_val:
            recommended_side = "SAMPLE"
        elif p_val > s_val:
            recommended_side = "SPECIMEN"
        else:
            recommended_side = "either (they are equal)"
        result_html += (
            f"<p><strong>Recommendation:</strong> Team {my_team} should play as {recommended_side} "
            f"(Sample: {s_val}, Specimen: {p_val}).</p>"
        )
        result_html += "</div>"
    else:
        result_html += f"<div class='output-box'><p>Team {my_team} not found in the data.</p></div>"
    
    # Build list of all teams from the original CSV for the dropdown.
    df_all_teams = sorted(str(x).strip() for x in df[team_col].unique())
    
    return {
        "resultHTML": result_html,
        "teams": df_all_teams,
        "removedTeams": current_removed
    }

def is_top_pair_unbeatable(pair_details):
    """
    Returns True if the top pair (first element in the sorted list) has a combined OPR
    that no other pair matches or exceeds.
    """
    if not pair_details:
        return False
    best_score = pair_details[0][4]
    for pd_ in pair_details[1:]:
        if pd_[4] >= best_score:
            return False
    return True

if __name__ == '__main__':
    app.run(debug=True)
