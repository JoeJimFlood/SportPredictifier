import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import xlsxwriter
from math import log2

def generate_report(fp, teams, results):
    
    book = xlsxwriter.Workbook(fp)

    # Formatting
    header_format = book.add_format({'align': 'center', 'bold': True, 'bottom': True})
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
    sheet.write_string(1, 0, 'City', index_format)
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
        team1win = probwin[team1]
        team2win = probwin[team2]
        draw = 1 - team1win - team2win

        p1 = team1win/(1-draw)
        p2 = team2win/(1-draw)
        entropy = -p1*log2(p1) - p2*log2(p2)
        #hype = 100*ranking_factor*entropy

        sheet.merge_range(1, team1col, 1, team2col, results[result]['venue'].location, merged_format)
        #sheet.merge_range(2, team1col, 2, team2col, ranking_factor, merged_format2)
        sheet.merge_range(3, team1col, 3, team2col, entropy, merged_format2)
        #sheet.merge_range(4, team1col, 4, team2col, hype, merged_format)

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