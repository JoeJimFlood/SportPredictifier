import SportPredictifier as sp
import os

base_path = os.path.dirname(__file__)
stadium_file = os.path.join(base_path, 'stadia.csv')
team_file = os.path.join(base_path, 'teams.csv')
score_table_path = os.path.join(base_path, 'ScoreTables')

stadia = sp.load.stadia(stadium_file)
teams = sp.load.teams(team_file, stadia)
score_tables = sp.load.score_tables(score_table_path)

for team in teams:
    print(team, teams[team].name, teams[team].stadium.lat, teams[team].stadium.lon)

print(score_tables.keys())