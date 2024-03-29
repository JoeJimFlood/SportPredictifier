import SportPredictifier as sp
import os

base_path = os.path.dirname(__file__)
#stadium_file = os.path.join(base_path, 'stadia.csv')
#team_file = os.path.join(base_path, 'teams.csv')
#score_settings_file = os.path.join(base_path, 'scoring.csv')
#score_table_path = os.path.join(base_path, 'ScoreTables')

#stadia = sp.load.stadia(stadium_file)
#teams = sp.load.teams(team_file, stadia)
#score_settings = sp.load.score_settings(score_settings_file)
#score_tables = sp.load.score_tables(score_table_path)

#sp.load.get_team_stats(teams, score_settings, score_tables)
#sp.load.get_opponent_stats(teams, score_settings, score_tables)
#sp.load.get_residual_stats(teams, score_settings, score_tables)
settings_file = os.path.join(base_path, 'settings.yaml')
settings = sp.load.settings(settings_file)
(stadia, teams, score_settings) = sp.load.data(settings)
schedule = sp.load.schedule(settings, teams, stadia, score_settings)

for team in teams:
    print(team, teams[team].name, teams[team].stadium.lat, teams[team].stadium.lon, teams[team].stadium.elev)
    for score_type in score_settings:
        print(score_type,
              teams[team].stats['F'][score_type],
              teams[team].stats['A'][score_type],
              teams[team].stats['F']['RES_' + score_type],
              teams[team].stats['A']['RES_' + score_type])
    print('\n')

for score in score_settings:
    print(score, score_settings[score].points)

for game in schedule.values():
    print('Week {} on {} at {} between {} and {}'.format(game.round_number,
                                                         game.date.strftime('%D'),
                                                         game.venue.name,
                                                         game.team1.name,
                                                         game.team2.name))