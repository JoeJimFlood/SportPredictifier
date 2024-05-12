import sys
import os
from . import load
from . import calculate
from .report import generate_report, generate_pie_charts, store_simulation_results
from .ranking import rank
from .util import run_multithreaded_games
from .matrix import generate_schedule, write_matrix

def initialize_season():
    '''
    Initializes a season by creating empty score tables based on the teams and the schedule.
    Can be called from the command line by typing `SportPredictifier initialize_season`
    '''
    print('Initializing Season')
    season_settings = load.settings('settings.yaml')
    (stadia, teams, score_settings) = load.data(season_settings, initializing_season = True)
    create_score_tables(season_settings, teams, stadia, score_settings)

def predictify(round_number):
    '''
    Simulates all of the games of a given round. Can be called from the command line by typing `SportPredictifier predictify [round_number]`

    Parameters
    ----------
    round_number (int):
        Round number to use in simulation
    '''
    season_settings = load.settings('settings.yaml')
    print('Predictifying {0} {1} {2}'.format(season_settings['name'], season_settings['round_name'], round_number))
    (stadia, teams, score_settings) = load.data(season_settings, round_number, '{0} < {1}'.format(season_settings['round_name'].upper(), round_number))

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
    round_schedule = load.schedule(season_settings, teams, stadia, score_settings, round_number = round_number, multithreaded = True, result_dict = results)

    run_multithreaded_games(round_schedule)

    calculate.hype(season_settings, results, round_number)

    outfile = os.path.join(season_settings['output_directory'], (season_settings['report_filename'] + '.xlsx').format(round_number))
    plotfile = os.path.join(season_settings['output_directory'], (season_settings['plot_filename'] + '.png').format(round_number))

    if 'store_simulation_results' in season_settings and season_settings["store_simulation_results"]:
        store_simulation_results(
            os.path.join(
            season_settings['output_directory'],
            "{0}{1}Simulations".format(
                season_settings['round_name'],
                round_number
                )),
                results
                )

    generate_report(outfile, teams, results)
    generate_pie_charts(plotfile, teams, results, season_settings['round_name'], round_number)

def matrix(outfile = 'matrix.csv'):
    '''
    Runs a matrix analysis by simulating a game between every remaining team, as specified by matrix.yaml.
    This creates a matrix with the chance of each team beating the other.
    Can be called from the command line by typing `SportPredictifier matrix [outfile]`

    Parameters
    ----------
    outfile (str):
        Outfile to write matrix to
    '''
    print("Creating Matrix")
    season_settings = load.settings('settings.yaml')
    matrix_settings = load.settings('matrix.yaml')
    (stadia, teams, score_settings) = load.data(season_settings, matrix_settings['round_number'])

    matrix_schedule = generate_schedule(matrix_settings, teams)

    print("Setting up matchups")
    matchups = []
    results = {}

    for round_number in matrix_schedule['round_number'].value_counts().index:
        (stadia, teams, score_settings) = load.data(season_settings, round_number, drop_null_score_table_records = True)
        matchups += load.schedule(season_settings, teams, stadia, score_settings, round_number, multithreaded = True, result_dict = results, schedule_override = matrix_schedule)

    print("Running matchups")
    run_multithreaded_games(matchups)

    print("Writing matrix")
    outfile = os.path.join(season_settings['output_directory'], (matrix_settings['outfile']))
    write_matrix(matrix_settings, results, outfile)

    print("Writing all results")
    outfile = os.path.join(season_settings['output_directory'], (season_settings['report_filename'] + '_matrix.xlsx'))
    generate_report(outfile, teams, results)

def main():
    '''
    The main function that calls either `initialize_season()`, `predictify()`, or `matrix()` depending on what the user specifies.
    '''
    if sys.argv[1] == 'initialize_season':
        initialize_season()

    elif sys.argv[1] == 'predictify':
        predictify(int(sys.argv[2]))

    elif sys.argv[1] == 'matrix':
        if len(sys.argv) > 2:
            matrix(sys.argv[2])
        else: # User did not specify outfile name
            matrix()