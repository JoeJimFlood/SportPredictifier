import SportPredictifier as sp
import os

base_path = os.path.dirname(__file__)
settings_file = os.path.join(base_path, 'settings.yaml')
settings = sp.load.settings(settings_file)
(stadia, teams, score_settings) = sp.load.data(settings)

results = {}
schedule = sp.load.schedule(settings, teams, stadia, score_settings, multithreaded = True, result_dict = results)

for game in schedule:
    game.join()

print(results)
print('Done')