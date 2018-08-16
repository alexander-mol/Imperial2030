import os
import logging
import time
import copy
import random

from path_config import ROOT_PATH
from game import Game
from base_player import BasePlayer
from advanced_player import SmartInvestor
import genetic_algorithm


num_games_to_run = 100

def collect_results(results, master_results):
    winner = sorted(list(results['player_scores'].items()), key=lambda x: -x[1])[0][0]
    master_results[winner] += 1

logging.basicConfig(filename=os.path.join(ROOT_PATH, 'log.txt'),
                    filemode='w',
                    # format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    format='%(message)s',
                    # datefmt='%H:%M:%S',
                    level=logging.DEBUG if num_games_to_run <= 10 else logging.ERROR)

def fitness_player_one(dna):
    player_list = [SmartInvestor('A', dna), BasePlayer('B'), BasePlayer('C'), BasePlayer('D')]
    master_results = {p.id: 0 for p in player_list}
    for _ in range(num_games_to_run):
        game = Game(players=copy.deepcopy(player_list))
        results = game.run()
        collect_results(results, master_results)
    return master_results['A'] / num_games_to_run * 100
random.seed(0)
base_dna = {'investor_own_interest_w': 0.346, 'investor_second_interest_w': 1.624, 'investor_const': 0.228, 'investor_tdp': -0.655, 'new_unit_prod_w': 1.442, 'existing_unit_prod_w': -0.562, 'production_const': 1.448, 'production_tdp': -0.075, 'unit_move_w': 0.778, 'maneuver_const': 0.952, 'maneuver_tdp': -0.029, 'tax_pp_w': 1.08, 'bonus_w': 0.874, 'taxation_const': 0.633, 'taxation_tdp': 1.055, 'factory_const': 2.6, 'factory_tdp': 0.306, 'ply_count_offset': 66.024, 'ply_count_w': 36.784, 'cash_w': -1.154, 'num_units_w': 1.448, 'tax_val_w': 4.449, 'vp_w': 1.83, 'RUSSIA': 8.391, 'CHINA': 9.82, 'INDIA': 11.136, 'BRAZIL': 21.774, 'USA': 9.641, 'EUROPE': 15.845}

genetic_algorithm.run_evolution(fitness_player_one, base_dna, recalculate=True)
# print(fitness_player_one(base_dna))
