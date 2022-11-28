import SportPredictifier as sp
import os

base_path = os.path.dirname(__file__)
stadium_file = os.path.join(base_path, 'stadia.csv')
team_file = os.path.join(base_path, 'teams.csv')

stadia = sp.load.stadia(stadium_file)
teams = sp.load.teams(team_file, stadia)

for team in teams:
    print(team, teams[team].name, teams[team].stadium.lat, teams[team].stadium.lon)