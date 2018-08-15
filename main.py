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


num_games_to_run = 1

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

base_dna = {'ply_count_offset': 57.208, 'ply_count_weight': 33.374, 'cash_weight': -1.251, 'num_units_weight': 1.079, 'tax_val_weight': 4.1, 'vp_weight': 1.568, 'RUSSIA': 9.432, 'CHINA': 6.907, 'INDIA': 9.969, 'BRAZIL': 20.5, 'USA': 9.071, 'EUROPE': 18.099}

# genetic_algorithm.run_evolution(fitness_player_one, base_dna, recalculate=True)
print(fitness_player_one(base_dna))
