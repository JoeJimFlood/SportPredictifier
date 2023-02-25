import os
from .load import *
from .report import generate_report
from .util import create_score_tables

def initialize_season():
    season_settings = settings('settings.yaml')
    (stadia, teams, score_settings) = data(season_settings, initializing_season = True)
    create_score_tables(season_settings, teams, stadia, score_settings)

def predictify(round_number):
    season_settings = settings('settings.yaml')
    (stadia, teams, score_settings) = data(season_settings, round_number)

    results = {}
    round_schedule = schedule(season_settings, teams, stadia, score_settings, round_number = round_number, multithreaded = True, result_dict = results)

    for game in round_schedule:
        game.join()

    outfile = os.path.join(season_settings['output_directory'], 'forecasts.xlsx')
    generate_report(outfile, teams, results)

def main():
    pass