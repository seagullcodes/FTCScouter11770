import pandas as pd
from itertools import combinations

# Use header=1 because the first row (row 0) is "2 Match1 ...", 
# and the second row (row 1) is the actual header row with "Team #, Name, Highest NP OPR..."
df = pd.read_csv("scouting.csv", header=1)

# Clean up column names (remove extra spaces, etc. using pandas yay
df.columns = df.columns.str.strip()

# columns init
team_col = "Team #"                 # team num
sample_opr_col = "Observed SAMPLEOPR"      # sample opr
specimen_opr_col = "Observed SPECIMEN OPR" # spec opr

# opr to numbers
df[sample_opr_col] = pd.to_numeric(df[sample_opr_col], errors='coerce').fillna(0)
df[specimen_opr_col] = pd.to_numeric(df[specimen_opr_col], errors='coerce').fillna(0)

# find and set best opr between spec and sample
df["Best OPR"] = df[[sample_opr_col, specimen_opr_col]].max(axis=1)

# pair best oprs with team numbers
# convert strings to numbers so if scouter makes mistake by adding something
df[team_col] = df[team_col].astype(str)
teams_dict = dict(zip(df[team_col], df["Best OPR"]))

# make every single pair possible (a little more than 800 for regionals)
all_pairs = list(combinations(teams_dict.keys(), 2))

# calc. each max opr per team combo
pair_scores = [(t1, t2, teams_dict[t1] + teams_dict[t2]) for t1, t2 in all_pairs]

# sort pairs and put high -> low
pair_scores.sort(key=lambda x: x[2], reverse=True)

# Print top 10 pairs
print("Top Team Combinations by Combined OPR:")
for i, (team1, team2, combined) in enumerate(pair_scores, start=1):
    print(f"{i}. Teams {team1} & {team2} => {combined:.2f}")

# Identify best partners for your team
my_team = "11770.0"  # Keep it as a string to match the dictionary keys
#print(teams_dict)
if my_team in teams_dict:
    partners = []
    for t in teams_dict:
        if t != my_team:
            combined_opr = teams_dict[my_team] + teams_dict[t]
            partners.append((t, combined_opr))
    # Sort best partners
    partners.sort(key=lambda x: x[1], reverse=True)

    print(f"\nBest Partners for Team {my_team}:")
    for i, (t, c) in enumerate(partners[:12], start=1):
        print(f"{i}. Team {t} => {c:.2f}")
else:
    print(f"\nTeam {my_team} not found in the data.")

def is_top_pair_unbeatable(pair_scores):
    """
    Returns True if the top pair (first element in the sorted list) has a combined OPR that
    no other pair matches or exceeds. Assumes pair_scores is sorted in descending order.
    """
    if not pair_scores:
        return False  # No pairs to compare

    best_score = pair_scores[0][2]
    # For a single pair, it's unbeatable by default.
    if len(pair_scores) == 1:
        return True

    # Check that no other pair matches or exceeds the best score
    return all(score < best_score for _, _, score in pair_scores[1:])

if is_top_pair_unbeatable(pair_scores):
    print("The top team combination is unbeatable.")
else:
    print("Another team combination can beat the top pair.")

def get_team_pair_rank(my_team, pair_scores, teams_dict):
    """
    Returns the rank (1-indexed) of the pairing of my_team with its best partner
    among all team combinations. The best partner is determined by the highest combined OPR.
    
    Parameters:
        my_team (str): The team number as a string (e.g., "11770").
        pair_scores (list of tuples): Each tuple is (team1, team2, combined_OPR)
            and the list is sorted in descending order by combined_OPR.
        teams_dict (dict): Dictionary mapping team numbers (as strings) to their Best OPR.
    
    Returns:
        int or None: Rank (starting at 1) of the my_team-best partner pair among all pairs,
                     or None if my_team is not in teams_dict.
    """
    if my_team not in teams_dict:
        return None

    # Find the best partner for my_team by maximizing the combined OPR.
    best_partner = None
    best_score = -float('inf')
    for team, opr in teams_dict.items():
        if team == my_team:
            continue
        combined = teams_dict[my_team] + opr
        if combined > best_score:
            best_score = combined
            best_partner = team

    # Search through the sorted pair_scores for the pair that matches {my_team, best_partner}.
    for rank, (t1, t2, score) in enumerate(pair_scores, start=1):
        if {t1, t2} == {my_team, best_partner}:
            return rank

    return None  # Should not reach here if the team is present and pair_scores is complete.
rank = get_team_pair_rank(my_team, pair_scores, teams_dict)
if rank is not None:
    print(f"The pairing of team {my_team} with its best partner is ranked #{rank} in combined OPR.")
else:
    print(f"Team {my_team} not found in the data.")


