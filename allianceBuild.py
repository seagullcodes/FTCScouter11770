from flask import Flask, request, jsonify, session
import pandas as pd
import io

app = Flask(__name__)
app.secret_key = "CHANGE_ME_TO_SOMETHING_RANDOM"  # For production, use a secure key

HTML_CODE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Alliance Builder</title>
  <style>
    body { 
      font-family: Arial, sans-serif; 
      margin: 20px;
      background-color: #f4f4f4;
    }
    .container { 
      max-width: 1200px; 
      margin: auto; 
      background: #fff; 
      padding: 20px; 
      border-radius: 5px; 
      box-shadow: 0 0 10px rgba(0,0,0,0.1); 
    }
    h1, h2 { text-align: center; }
    form { margin-bottom: 20px; }
    input[type="file"], select, button { 
      padding: 8px; 
      margin: 5px 0; 
      border: 1px solid #333;
      border-radius: 3px;
      display: block;
      width: 100%;
      box-sizing: border-box;
    }
    button { 
      background-color: #007acc; 
      color: #fff; 
      cursor: pointer;
    }
    button:hover { background-color: #005f99; }
    .builder-container {
      display: flex;
      justify-content: space-between;
      gap: 20px;
      margin-top: 20px;
      flex-wrap: wrap;
    }
    .box {
      border: 2px solid #007acc;
      border-radius: 5px;
      padding: 15px;
      background-color: #f9f9f9;
      flex: 1 1 30%;
      min-width: 280px;
    }
    .box h2 {
      margin-top: 0;
      font-size: 1.2em;
      border-bottom: 1px solid #007acc;
      padding-bottom: 5px;
    }
    ul {
      list-style: none;
      padding-left: 0;
    }
    ul li {
      padding: 5px;
      margin: 5px 0;
      background-color: #e6e6e6;
      border-radius: 3px;
      cursor: pointer;
    }
    ul li:hover {
      background-color: #d4d4d4;
    }
    #selectedTeams li {
      cursor: default;
    }
    .alliance-item {
      border: 1px solid #ccc;
      padding: 5px;
      margin-bottom: 5px;
      border-radius: 3px;
      background-color: #e0f7fa;
      position: relative;
    }
    .remove-btn {
      float: right;
      top: 5px;
      right: 5px;
      background-color: #e53935;
      color: #fff;
      border: none;
      border-radius: 3px;
      padding: 3px 6px;
      cursor: pointer;
      font-size: 0.8em;
    }
    .remove-btn:hover {
      background-color: #b71c1c;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>my super cool alliance builder that will workr</h1>
    <!-- CSV Upload Form -->
    <form id="csvForm" method="POST" enctype="multipart/form-data">
      <label for="csvFile">Upload CSV file:</label>
      <input type="file" id="csvFile" name="csvFile" accept=".csv">
      <button type="submit">Upload CSV</button>
    </form>
    
    <!-- Built Alliances Section (displayed at the top) -->
    <div id="builtAlliancesSection" style="display:none;">
      <h2>Formed Alliances</h2>
      <ul id="alliancesList"></ul>
    </div>
    
    <!-- Alliance Builder UI; hidden until CSV is uploaded -->
    <div id="allianceBuilder" style="display:none;">
      <div>
        <label for="sortCriteria">Sort Teams By:</label>
        <select id="sortCriteria">
          <option value="sample" selected>Sample OPR</option>
          <option value="specimen">Spec OPR</option>
        </select>
      </div>
      
      <div class="builder-container">
        <!-- Left side: Available teams list -->
        <div id="availableTeams" class="box">
          <h2>Available Teams</h2>
          <ul id="teamsList"></ul>
        </div>
        
        <!-- Center: Current alliance selection -->
        <div id="currentAlliance" class="box">
          <h2>Current Alliance</h2>
          <p>Select two teams to form an alliance:</p>
          <ul id="selectedTeams"></ul>
          <button id="buildAlliance" type="button" disabled>add this alliance!</button>
          <button id="clearSelection" type="button">clear the current alliance you are working on</button>
        </div>
      </div>
    </div>
  </div>
  
  <script>
    // Global variables to store team and alliance data.
    let teamsData = {};          // { teamNum: { sample: number, specimen: number } }
    let availableTeams = [];     // Teams available for alliance formation.
    let currentSelection = [];   // Temporary selection for a two–team alliance.
    let alliances = [];          // List of formed alliances.

    // Render the list of available teams, sorted based on the chosen criterion.
    function renderAvailableTeams() {
      const teamsList = document.getElementById('teamsList');
      teamsList.innerHTML = "";
      const sortCriteria = document.getElementById('sortCriteria').value;
      // Sort available teams by the chosen OPR (descending)
      let sorted = availableTeams.slice().sort((a, b) => teamsData[b][sortCriteria] - teamsData[a][sortCriteria]);
      sorted.forEach(team => {
        let li = document.createElement('li');
        li.textContent = team + " (Sample: " + teamsData[team].sample + ", Specimen: " + teamsData[team].specimen + ")";
        li.addEventListener("click", () => selectTeam(team));
        teamsList.appendChild(li);
      });
    }
    
    // Render the current selection (teams that have been clicked for an alliance)
    function renderCurrentSelection() {
      const selectedList = document.getElementById('selectedTeams');
      selectedList.innerHTML = "";
      currentSelection.forEach(team => {
        let li = document.createElement('li');
        li.textContent = team;
        selectedList.appendChild(li);
      });
      // Enable the "Build Alliance" button only when exactly 2 teams are selected.
      document.getElementById('buildAlliance').disabled = (currentSelection.length !== 2);
    }
    
    // Render the formed alliances sorted by best combined OPR.
    function renderAlliances() {
      const alliancesList = document.getElementById('alliancesList');
      alliancesList.innerHTML = "";
      // Sort alliances by best combined OPR descending
      let sortedAlliances = alliances.slice().sort((a, b) => b.bestScore - a.bestScore);
      sortedAlliances.forEach((alliance, index) => {
        let li = document.createElement('li');
        li.className = "alliance-item";
        li.innerHTML = "<strong>" + alliance.teams[0] + " & " + alliance.teams[1] + "</strong> => Combined OPR: " + alliance.bestScore.toFixed(2) + "<br><small>" + alliance.details + "</small>";
        
        // Remove alliance button
        let removeBtn = document.createElement('button');
        removeBtn.textContent = "Remove Alliance";
        removeBtn.className = "remove-btn";
        removeBtn.addEventListener("click", () => removeAlliance(alliance));
        li.appendChild(removeBtn);
        
        alliancesList.appendChild(li);
      });
    }
    
    // Called when a team is clicked from the available list.
    function selectTeam(team) {
      if (currentSelection.includes(team)) return;
      if (currentSelection.length >= 2) return;
      currentSelection.push(team);
      renderCurrentSelection();
    }
    
    // Form an alliance from currentSelection when the button is clicked.
    function formAlliance() {
      if (currentSelection.length !== 2) return;
      let team1 = currentSelection[0];
      let team2 = currentSelection[1];
      
      // Calculate both options:
      let optionA = teamsData[team1].sample + teamsData[team2].specimen;
      let optionB = teamsData[team1].specimen + teamsData[team2].sample;
      let bestScore = Math.max(optionA, optionB);
      let option = (optionA >= optionB) ? "A" : "B";
      let details = (option === "A") ?
          (team1 + " as SAMPLE (" + teamsData[team1].sample + ") + " + team2 + " as SPECIMEN (" + teamsData[team2].specimen + ")") :
          (team1 + " as SPECIMEN (" + teamsData[team1].specimen + ") + " + team2 + " as SAMPLE (" + teamsData[team2].sample + ")");
      
      alliances.push({
        teams: [team1, team2],
        bestScore: bestScore,
        option: option,
        details: details
      });
      
      // Remove the two teams from available teams.
      availableTeams = availableTeams.filter(t => t !== team1 && t !== team2);
      
      // Reset current selection.
      currentSelection = [];
      
      renderCurrentSelection();
      renderAvailableTeams();
      renderAlliances();
      // Make sure the built alliances section is visible.
      document.getElementById('builtAlliancesSection').style.display = "block";
    }
    
    // Remove an alliance and add its teams back to available teams.
    function removeAlliance(alliance) {
      // Remove alliance from the alliances array.
      alliances = alliances.filter(a => a !== alliance);
      // Add the teams back to availableTeams if not already there.
      alliance.teams.forEach(team => {
        if (!availableTeams.includes(team)) {
          availableTeams.push(team);
        }
      });
      renderAvailableTeams();
      renderAlliances();
    }
    
    // Event listeners for build alliance button, clearing selection, and changing sort order.
    document.getElementById('buildAlliance').addEventListener("click", function() {
      formAlliance();
    });
    
    document.getElementById('clearSelection').addEventListener("click", function() {
      currentSelection = [];
      renderCurrentSelection();
    });
    
    document.getElementById('sortCriteria').addEventListener("change", function() {
      renderAvailableTeams();
    });
    
    // Handle CSV file upload.
    document.getElementById('csvForm').addEventListener("submit", function(e) {
      e.preventDefault();
      let fileInput = document.getElementById('csvFile');
      if (!fileInput.files || fileInput.files.length === 0) {
        alert("Please select a CSV file.");
        return;
      }
      let file = fileInput.files[0];
      let formData = new FormData();
      formData.append("csvFile", file);
      
      fetch("/upload", { method: "POST", body: formData })
        .then(response => response.json())
        .then(data => {
          if(data.error){
            alert(data.error);
            return;
          }
          // The server returns an object mapping team numbers to their OPR values.
          teamsData = data.teamsData;
          availableTeams = Object.keys(teamsData);
          currentSelection = [];
          alliances = [];
          document.getElementById('allianceBuilder').style.display = "block";
          renderAvailableTeams();
          renderCurrentSelection();
          renderAlliances();
        })
        .catch(err => {
          alert("Error uploading CSV: " + err);
        });
    });
  </script>
</body>
</html>
"""

@app.route('/')
def index():
    return HTML_CODE

@app.route('/upload', methods=["POST"])
def upload():
    """
    Handles CSV file uploads. The CSV file should contain the following columns:
      - "Team #"
      - "Observed SAMPLEOPR"
      - "Observed SPECIMEN OPR"
    The CSV is parsed, and a dictionary of team data is returned in JSON.
    """
    file = request.files.get("csvFile")
    if not file or file.filename == "":
        return jsonify({"error": "No file provided"}), 400
    try:
        # Assuming the CSV has a header row that starts on the second row (header=1)
        df = pd.read_csv(file, header=1)
    except Exception as e:
        return jsonify({"error": f"Error reading CSV: {e}"}), 400
    
    df.columns = df.columns.str.strip()
    team_col = "Team #"
    sample_opr_col = "Observed SAMPLEOPR"
    specimen_opr_col = "Observed SPECIMEN OPR"
    
    # Convert the OPR columns to numbers.
    df[sample_opr_col] = pd.to_numeric(df[sample_opr_col], errors='coerce').fillna(0)
    df[specimen_opr_col] = pd.to_numeric(df[specimen_opr_col], errors='coerce').fillna(0)
    
    teamsData = {}
    for _, row in df.iterrows():
        team_str = str(row[team_col]).strip()
        teamsData[team_str] = {
            "sample": row[sample_opr_col],
            "specimen": row[specimen_opr_col]
        }
    return jsonify({"teamsData": teamsData})

if __name__ == '__main__':
    app.run(debug=True)
