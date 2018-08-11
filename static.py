RONDEL_POSITIONS = {0: 'Investor', 1: 'Import', 2: 'Production', 3: 'Maneuver', 4: 'Taxation', 5: 'Factory',
                    6: 'Production', 7: 'Maneuver'}
NATION_TURN_LIST = ['RUSSIA', 'CHINA', 'INDIA', 'BRAZIL', 'USA', 'EUROPE']
TAX_BENEFIT = {
    'buckets': [6, 8, 10, 11, 12, 13, 14, 15, 16, 18],
    'bonus': [0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5],
    'power': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
}
BOND_VALUE_TO_INTEREST = {2: 1, 4: 2, 6: 3, 9: 4, 12: 5, 16: 6, 20: 7, 25: 8, 30: 9}

NUM_PLAYERS_TO_PLAYER_STARTING_MONEY = {2: 35, 3: 24, 4: 13, 5: 13, 6: 13}

STARTING_NATION_SECOND_INVESTMENT = \
    {'RUSSIA': 'EUROPE', 'CHINA': 'USA', 'INDIA': 'BRAZIL', 'BRAZIL': 'CHINA', 'USA': 'RUSSIA', 'EUROPE': 'INDIA'}

# single values
STARTING_INVESTMENT = 9
SECONDARY_INVESTMENT = 2
FACTORY_COST = 5
IMPORT_COST_PER_UNIT = 1
MAX_IMPORT = 3
BEFORE_INVEST_BONUS = 2

TAXATION_COST_PER_UNIT = 1
TAXATION_VALUE_OF_FACTORY = 2
TAXATION_VALUE_OF_FLAG = 1
