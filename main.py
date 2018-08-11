import os
import logging
import time
import random

from path_config import ROOT_PATH
from game import Game
from base_player import BasePlayer

logging.basicConfig(filename=os.path.join(ROOT_PATH, 'log.txt'),
                    filemode='w',
                    # format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    format='%(message)s',
                    # datefmt='%H:%M:%S',
                    level=logging.DEBUG)


player_list = [BasePlayer('A'), BasePlayer('B'), BasePlayer('C'), BasePlayer('D')]

random.seed(0)
game = Game(players=player_list)

t0 = time.time()
print(game.run())
print(f'{time.time() - t0:.3f} s')
