import pandas as pd
from .util import directions, compliment_direction

def check_teams_and_venues(errors, score_tables, teams, stadia, settings):
    '''
    Checks that the teams and venues listed in the score table exist
    '''
    for team in score_tables:
        current_table = score_tables[team].copy()
        #assert current_table['OPP'].apply(lambda x: x != team).all() # Checking that a team isn't recorded as playing against themselves
        #assert current_table['OPP'].isin(teams.keys()).all() # Check if all opponents are valid
        #assert current_table['VENUE'].isin(stadia.keys()).all() # Check if all venues are valid
        for ix, row in current_table.iterrows():
            if row['OPP'] == team:
                errors.append("{0} is recorded as playing against themselves in {1} {2}".format(team,
                                                                                                settings['round_name'],
                                                                                                row[settings['round_name'].upper()]))
            if row['OPP'] not in teams.keys():
                errors.append("{0} is not a valid opponent for {1} in {2} {3}".format(row['OPP'],
                                                                                      team,
                                                                                      settings['round_name'],
                                                                                      row[settings['round_name'].upper()]))
            if row['VENUE'] not in stadia.keys():
                errors.append("{0} is not a valid venue for {1} in {2} {3}".format(row['VENUE'],
                                                                                   team,
                                                                                   settings['round_name'],
                                                                                   row[settings['round_name'].upper()]))

    return errors

def check_consistency(errors, score_tables, score_settings, settings):
    '''
    Checks for consistency between score tables
    '''
    # Create large data frame for mapping
    scores_for = pd.DataFrame()
    for team in score_tables:
        current_table = score_tables[team].copy()
        current_table['TEAM'] = team
        scores_for = pd.concat((scores_for, current_table))
    scores_for['INDEX'] = scores_for['TEAM'] + scores_for[settings['round_name'].upper()].astype(str)
    scores_for = scores_for.set_index('INDEX')

    for team in score_tables:
        current_team = score_tables[team].copy()
        for score_type in score_settings:
            
            current_team['OPPLOOKUP'] = current_team['OPP'] + current_team[settings['round_name'].upper()].astype(str)
            score_type_check = current_team[score_type + '_A'] != current_team['OPPLOOKUP'].map(scores_for[score_type + '_F'])
            if sum(score_type_check) > 0:
                problems = current_team[score_type_check].copy()
                for (ix, row) in problems.iterrows():
                    errors.append("Mismatch in {0} in {1} {2} entry between {3} and {4}".format(score_type,
                                                                                                settings['round_name'],
                                                                                                row[settings['round_name'].upper()],
                                                                                                team,
                                                                                                row['OPP']))

    del scores_for, current_team
    return errors

def check_validity(errors, score_tables, score_settings, settings):
    '''
    Checks if every probabilistic score type is not greater than the condition
    '''
    for score_type in score_settings:
        for team in score_tables:
            current_team = score_tables[team].copy()

            if score_settings[score_type].prob:

                current_team['condition'] = current_team.eval(score_settings[score_type].condition.replace('{F}', 'F').replace('{A}', 'A'))
                current_team['invalid'] = (current_team[score_type + '_F'] > current_team['condition'])

                if current_team['invalid'].sum() == 0:
                    continue

                problems = current_team.query('invalid')
                for (ix, row) in problems.iterrows():
                    errors.append('Invalid condition for {0} in {1} {2} of score table for {3}'.format(score_type + "_F",
                                                                                                        settings["round_name"],
                                                                                                        row[settings['round_name'].upper()],
                                                                                                        team))

            else:
                continue

    return errors
                
def validate_score_tables(score_tables, score_settings, teams, stadia, settings):
    print("Validating score tables")
    errors = []
    errors = check_teams_and_venues(errors, score_tables, teams, stadia, settings)
    errors = check_consistency(errors, score_tables, score_settings, settings)
    errors = check_validity(errors, score_tables, score_settings, settings)

    if len(errors) > 0:
        for error in errors:
            print(error)
        raise IOError("Error(s) present in score tables")