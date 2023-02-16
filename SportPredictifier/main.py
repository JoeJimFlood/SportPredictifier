import os
from .load import *
from .util import create_score_tables

def initialize_season():
    season_settings = settings('settings.yaml')
    (stadia, teams, score_settings) = data(season_settings, initializing_season = True)
    create_score_tables(season_settings, teams, stadia, score_settings)