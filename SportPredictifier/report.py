import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import xlsxwriter
from .util import get_plot_shape, get_font_size

def generate_report(fp, teams, results):
    '''
    Generates the report XLSX file that has the chances of each team winning, the hype, and the characteristics of the distribution of scores from the simulations.

    Parameters
    ----------
    fp (str):
        Filepath to write to
    teams (SportPredictifier.ObjectCollection):
        Collection of teams in the competition
    results (dict):
        Dictionary of simulation results
    '''
    print("Generating report")
    book = xlsxwriter.Workbook(fp, {'nan_inf_to_errors': True})

    # Formatting
    index_format = book.add_format({'align': 'right', 'bold': True})
    score_format = book.add_format({'num_format': '#0', 'align': 'right'})
    percent_format = book.add_format({'num_format': '#0%', 'align': 'right'})
    merged_format = book.add_format({'num_format': '#0.00', 'align': 'center'})
    merged_format2 = book.add_format({'num_format': '0.000', 'align': 'center'})
    team_formats = {}
    for team in teams:
        team_formats[team] = book.add_format({'align': 'center', 'bold': True, 'border': True,
                                              'bg_color': teams[team].color1, 'font_color': teams[team].color2})

    sheet = book.add_worksheet("Forecasts") # TODO: Make configurable to put different games on different sheets

    # Write labels
    sheet.write_string(1, 0, 'Location', index_format)
    sheet.write_string(2, 0, 'Quality', index_format)
    sheet.write_string(3, 0, 'Entropy', index_format)
    sheet.write_string(4, 0, 'Hype', index_format)
    sheet.write_string(5, 0, 'Chance of Winning', index_format)
    sheet.write_string(6, 0, 'Expected Score', index_format)
    for i in range(1, 20):
        sheet.write_string(6+i, 0, str(5*i) + 'th Percentile Score', index_format)
    sheet.freeze_panes(0, 1)

    sheet.set_column(0, 0, 20)

    i = 0
    for result in results:
        (team1, team2) = result.split('v')
        team1col = 3*i+1
        team2col = 3*i+2
        sheet.write_string(0, team1col, team1, team_formats[team1])
        sheet.write_string(0, team2col, team2, team_formats[team2])
        probwin = results[result]['chances']

        sheet.merge_range(1, team1col, 1, team2col, results[result]["venue"].location, merged_format)
        try:
            sheet.merge_range(2, team1col, 2, team2col, results[result]["quality"], merged_format2)
            sheet.merge_range(3, team1col, 3, team2col, results[result]["entropy"], merged_format2)
            sheet.merge_range(4, team1col, 4, team2col, results[result]["hype"], merged_format)
        except KeyError:
            pass

        sheet.write_number(5, team1col, probwin[team1], percent_format)
        sheet.write_number(5, team2col, probwin[team2], percent_format)
        team1_dist = results[result]['score_distributions'][team1]
        team2_dist = results[result]['score_distributions'][team2]

        sheet.write_number(6, team1col, team1_dist['mean'], score_format)
        sheet.write_number(6, team2col, team2_dist['mean'], score_format)
        for j in range(1, 20):
            sheet.write_number(6+j, team1col, team1_dist[str(5*j)+'%'], score_format)
            sheet.write_number(6+j, team2col, team2_dist[str(5*j)+'%'], score_format)

        sheet.set_column(team1col, team2col, 7.5)
        sheet.set_column(team2col+1, team2col+1, 1)

        i += 1

    book.close()

def __plot_pie_chart_group(fp, teams, group_results, round_name, round_number):
    '''
    Plots pie charts for a group to be in the image

    Parameters
    ----------
    fp (str):
        Filepath to save plots to
    teams (SportPredictifier.ObjectCollection):
        Collection of teams in the competition
    group_results (dict):
        Results of games assigned to this group to be plotted
    round_name (str):
        The name of a round as defined in settings.yaml
    round_number (int):
        The round number of the games being shown
    '''
    n_games_in_group = len(group_results)
    plot_shape = get_plot_shape(n_games_in_group)
    
    font_size = get_font_size(n_games_in_group)

    plt.figure(figsize = (15, 15), dpi = 96)
    plt.axis("off")
    counter = 0
    for result in group_results:
        (team1, team2) = result.split("v")
        stadium = group_results[result]["venue"].name
        location = group_results[result]["venue"].location
        hype = group_results[result]["hype"]

        team1win = group_results[result]["chances"][team1]
        team2win = group_results[result]["chances"][team2]
        draw = 1 - team1win - team2win

        counter += 1

        if n_games_in_group == 5 and counter == 5:
            plot_pos = 6
        elif n_games_in_group == 7 and counter == 7:
            plot_pos = 8
        elif n_games_in_group == 8 and counter == 8:
            plot_pos = 9
        else:
            plot_pos = counter

        plt.subplot(plot_shape[0], plot_shape[1], plot_pos)

        if draw < 2**-23:
            labels = [team1, team2]
            values = [team1win, team2win]
            colors1 = [teams[team1].color1, teams[team2].color1]
            colors2 = [teams[team1].color2, teams[team2].color2]
            explode = 2*[0.05]
        else:
            labels = [team1, team2, "DRAW"]
            values = [team1win, team2win, draw]
            colors1 = [teams[team1].color1, teams[team2].color1, "#808080"]
            colors2 = [teams[team1].color2, teams[team2].color2, "#808080"]
            explode = 3*[0.05]

        patches = plt.pie(
            values,
            colors = colors1,
            labels = labels,
            explode = explode,
            autopct='%.0f%%',
            startangle = 90,
            labeldistance = 1,
            textprops = {'backgroundcolor': '#ffffff', 'ha': 'center', 'va': 'center', 'fontsize': font_size}
            )

        for i in range(len(patches[0])):
            patches[0][i].set(edgecolor = colors2[i], hatch = '/')
            patches[1][i].set(bbox = {'facecolor': 'w', 'edgecolor': 'k'})
            patches[2][i].set(bbox = {'facecolor': 'w', 'edgecolor': 'k'})

        title_lines = [
            '{0} vs {1}'.format(teams[team1].name, teams[team2].name),
            stadium,
            location,
            'Hype: {}'.format(int(round(hype, 0)))
            ]
        
        if n_games_in_group == 1:
            plt.title('\n'.join(title_lines), size = font_size, y = 0.905)
        else:
            plt.title('\n'.join(title_lines), size = font_size)
        
    plt.savefig(fp)

def generate_pie_charts(fp, teams, results, round_name, round_number):
    '''
    Generates the pie charts that show the estimated chances of each team winning each game

    Parameters
    ----------
    fp (str):
        Filepath to save plots to
    teams (SportPredictifier.ObjectCollection):
        Collection of teams in the competition
    results (dict):
        Results of games to be plotted
    round_name (str):
        The name of a round as defined in settings.yaml
    round_number (int):
        The round number of the games being shown
    '''
    assert fp.endswith('.png'), "Outfile must be a PNG file"

    matchups = list(results.keys())
    n_games = len(matchups)
    n_groups = (n_games-1) // 9 + 1
    games_per_group = n_games // n_groups

    # Allocate results to plot group
    groups = []
    for i in range(n_groups):
        group = {}
        for j in range(games_per_group):
            ix = i*games_per_group + j
            if ix >= n_games:
                continue
            group[matchups[ix]] = results[matchups[ix]]
        groups.append(group)

    # Generate Plots
    if len(groups) == 1:
        __plot_pie_chart_group(
            fp,
            teams,
            groups[0],
            round_name,
            round_number
            )
    else:
        for i in range(len(groups)):
            __plot_pie_chart_group(
                fp.replace('.png', '_{}.png'.format(i+1)),
                teams,
                groups[i],
                round_name,
                round_number
                )
            
def store_simulation_results(dir, results):
    assert "scores" in results[list(results.keys())[0]], "Scores must be present in results to store them"

    # Check if path to keep results in exists, and if not make it
    if not os.path.isdir(dir):
        os.mkdir(dir)

    for matchup in results:
        print("Writing scores for " + matchup)
        results[matchup]["scores"].to_csv(os.path.join(dir, matchup + '_simresults.csv'))