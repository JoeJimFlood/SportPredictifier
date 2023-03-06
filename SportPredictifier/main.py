import sys
import os
from .load import *
from .report import generate_report
from .ranking import rank
from .util import create_score_tables, calculate_hype

def initialize_season():
    print('Initializing Season')
    season_settings = settings('settings.yaml')
    (stadia, teams, score_settings) = data(season_settings, initializing_season = True)
    create_score_tables(season_settings, teams, stadia, score_settings)

def predictify(round_number):
    season_settings = settings('settings.yaml')
    print('Predictifying {0} {1} {2}'.format(season_settings['name'], season_settings['round_name'], round_number))
    (stadia, teams, score_settings) = data(season_settings, round_number, 'ROUND < {}'.format(round_number))

    print('Ranking teams')
    rank(
        season_settings['score_table_path'],
        os.path.join(
            season_settings['ranking_directory'],
            season_settings['ranking_filename'].format(round_number) + '.csv'
            ),
        score_settings,
        round_number
        )

    results = {}
    round_schedule = schedule(season_settings, teams, stadia, score_settings, round_number = round_number, multithreaded = True, result_dict = results)

    for game in round_schedule:
        game.join()

    calculate_hype(season_settings, results, round_number)

    outfile = os.path.join(season_settings['output_directory'], (season_settings['report_filename'] + '.xlsx').format(round_number))
    generate_report(outfile, teams, results)

def main():
    if sys.argv[1] == 'initialize_season':
        initialize_season()
    elif sys.argv[1] == 'predictify':
        predictify(int(sys.argv[2]))