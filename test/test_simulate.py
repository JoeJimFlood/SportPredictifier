import SportPredictifier as sp
import os
import time

t0 = time.time()

ROUND_NUMBER = 1

base_path = os.path.dirname(__file__)
settings_file = os.path.join(base_path, 'settings.yaml')
settings = sp.load.settings(settings_file)
(stadia, teams, score_settings) = sp.load.data(settings, ROUND_NUMBER)

results = {}
schedule = sp.load.schedule(settings, teams, stadia, score_settings, round_number = ROUND_NUMBER, multithreaded = True, result_dict = results)

for game in schedule:
    game.join()

print(results)

t1 = time.time()

print('Done in {} seconds'.format(round(t1-t0, 1)))