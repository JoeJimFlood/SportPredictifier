import SportPredictifier as sp
import os
import time
import numpy as np

t0 = time.time()

base_path = os.path.dirname(__file__)
settings_file = os.path.join(base_path, 'settings.yaml')
settings = sp.load.settings(settings_file)

for ROUND_NUMBER in range(1, 4):
    round_in_table = ROUND_NUMBER + 18
    (stadia, teams, score_settings) = sp.load.data(settings, ROUND_NUMBER, 'ROUND < ' + str(round_in_table))

    results = {}
    schedule = sp.load.schedule(settings, teams, stadia, score_settings, round_number = ROUND_NUMBER, multithreaded = True, result_dict = results)

    for game in schedule:
        game.join()


    outfile = os.path.join(settings['output_directory'], 'forecasts_round_{}.xlsx'.format(ROUND_NUMBER))
    sp.report.generate_report(outfile, teams, results)

t1 = time.time()

print('Done in {} seconds'.format(round(t1-t0, 1)))