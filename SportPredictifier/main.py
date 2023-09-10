import sys
import os
from .load import *
from .report import generate_report, generate_pie_charts
from .ranking import rank
from .util import create_score_tables, calculate_hype, run_multithreaded_games
from .matrix import generate_schedule, write_matrix

def initialize_season():
    print('Initializing Season')
    season_settings = settings('settings.yaml')
    (stadia, teams, score_settings) = data(season_settings, initializing_season = True)
    create_score_tables(season_settings, teams, stadia, score_settings)

def predictify(round_number):
    season_settings = settings('settings.yaml')
    print('Predictifying {0} {1} {2}'.format(season_settings['name'], season_settings['round_name'], round_number))
    (stadia, teams, score_settings) = data(season_settings, round_number, '{0} < {1}'.format(season_settings['round_name'].upper(), round_number))

    print('Ranking teams')
    rank(
        season_settings['score_table_path'],
        os.path.join(
            season_settings['ranking_directory'],
            season_settings['ranking_filename'].format(round_number) + '.csv'
            ),
        score_settings,
        season_settings['round_name'],
        round_number
        )

    results = {}
    round_schedule = schedule(season_settings, teams, stadia, score_settings, round_number = round_number, multithreaded = True, result_dict = results)

    run_multithreaded_games(round_schedule)

    calculate_hype(season_settings, results, round_number)

    outfile = os.path.join(season_settings['output_directory'], (season_settings['report_filename'] + '.xlsx').format(round_number))
    plotfile = os.path.join(season_settings['output_directory'], (season_settings['plot_filename'] + '.png').format(round_number))
    generate_report(outfile, teams, results)
    generate_pie_charts(plotfile, teams, results, season_settings['round_name'], round_number)

def matrix(outfile = 'matrix.csv'):
    print("Creating Matrix")
    season_settings = settings('settings.yaml')
    matrix_settings = settings('matrix.yaml')
    (stadia, teams, score_settings) = data(season_settings, matrix_settings['round_number'])

    matrix_schedule = generate_schedule(matrix_settings, teams)

    print("Setting up matchups")
    matchups = []
    results = {}

    for round_number in matrix_schedule['round_number'].value_counts().index:
        #round_number = row['round_number']
        (stadia, teams, score_settings) = data(season_settings, round_number, drop_null_score_table_records = True)
        matchups += schedule(season_settings, teams, stadia, score_settings, round_number, multithreaded = True, result_dict = results, schedule_override = matrix_schedule)

    print("Running matchups")
    run_multithreaded_games(matchups)

    print("Writing matrix")
    outfile = os.path.join(season_settings['output_directory'], (matrix_settings['outfile']))
    write_matrix(matrix_settings, results, outfile)

    print("Writing all results")
    outfile = os.path.join(season_settings['output_directory'], (season_settings['report_filename'] + '_matrix.xlsx'))
    generate_report(outfile, teams, results)

def main():
    if sys.argv[1] == 'initialize_season':
        initialize_season()

    elif sys.argv[1] == 'predictify':
        predictify(int(sys.argv[2]))

    elif sys.argv[1] == 'matrix':
        if len(sys.argv) > 2:
            matrix(sys.argv[2])
        else: # User did not specify outfile name
            matrix()