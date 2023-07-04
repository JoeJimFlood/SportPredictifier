import pandas as pd
from .util import directions, compliment_direction

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
                    errors.append('Invalid condition for {0} in {1} {2} of Score Table for {3}'.format(score_type + "_F",
                                                                                                        settings["round_name"],
                                                                                                        row[settings['round_name'].upper()],
                                                                                                        team))

            else:
                continue

    return errors
                
def validate_score_tables(score_tables, score_settings, settings):
    print("Validating score tables")
    errors = []
    errors = check_consistency(errors, score_tables, score_settings, settings)
    errors = check_validity(errors, score_tables, score_settings, settings)

    if len(errors) > 0:
        for error in errors:
            print(error)
        raise IOError("Error(s) present in score tables")