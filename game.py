import random
import copy
import map
import nation
import static
import logging

logger = logging.getLogger(__name__)


# TODO write transact cash and transact bond methods so everything flows through there
class Game:

    def __init__(self, players):
        self.map = map.Map()
        self.nations = {n: nation.Nation(n, self.map) for n in static.NATION_TURN_LIST}
        self.players = players
        self.next_investor_player_index = 0
        self.nation_to_player_map = {}
        self.active_nation = self.nations['RUSSIA']
        self.bonds_by_player_by_nation = {player.id: {n: [] for n in self.nations} for player in self.players}
        self.ply_count = 0

    def run(self):
        self.initialize()
        # handle first moves - initial rondel positions
        for _ in static.NATION_TURN_LIST:
            if self.active_nation.name not in self.nation_to_player_map:  # if nobody owns the nation
                self.update_active_nation()
                continue
            initial_command = self.nation_to_player_map[self.active_nation.name].get_initial_command(self)
            self.execute_command(initial_command, first_command=True)
            self.update_active_nation()
            logger.info(f"Player money: { {p.id: p.cash for p in self.players}}")
            logger.info(f"Nation money: { {n.name: n.cash for n in self.nations.values()}}")
            logger.info(f"Nation tax val: "
                        f"{ {n.name: n.get_taxation_value() for n in self.nations.values()}}")
            logger.info(f"Nation power points: { {n.name: n.vp for n in self.nations.values()}}")
            logger.info(f"Nation units: { {n.name: n.get_units() for n in self.nations.values()}}")

        while not self.game_finished():
            if self.active_nation.name not in self.nation_to_player_map:  # if nobody owns the nation
                self.update_active_nation()
                continue
            self.map.refresh(self.active_nation.name)
            command = self.nation_to_player_map[self.active_nation.name].get_turn_command(self)
            self.execute_command(command)
            self.update_active_nation()
            logger.info(f"Player money: { {p.id: p.cash for p in self.players}}")
            logger.info(f"Nation money: { {n.name: n.cash for n in self.nations.values()}}")
            logger.info(f"Nation tax val: "
                        f"{ {n.name: n.get_taxation_value() for n in self.nations.values()}}")
            logger.info(f"Nation power points: { {n.name: n.vp for n in self.nations.values()}}")
            logger.info(f"Nation units: { {n.name: n.get_units() for n in self.nations.values()}}")

        results = {'player_scores': {player.id: player.get_current_vp(self) for player in self.players},
                   'country_power': {n.name: n.vp for n in self.nations.values()},
                   'ply_count': self.ply_count
        }
        logger.info(results)
        return results

    def initialize(self):
        # initialize player money, nation money
        for player in self.players:
            player.mutate_cash(static.NUM_PLAYERS_TO_PLAYER_STARTING_MONEY[len(self.players)])
        # create starting factories
        for territory_name, territory in self.map.territories.items():
            if territory['initial_factory']:
                self.map.create_factory(territory['name'])
        # initialize nation to player map
        # TODO This assumes more than 3 players - implement properly for 2, 3 players
        # randomly distribute one nation to each player
        nations = copy.copy(static.NATION_TURN_LIST)
        random.shuffle(nations)
        for player in self.players:
            nation_name = nations.pop()
            self.nations[nation_name].transact_bond(value=static.STARTING_INVESTMENT)
            player.transact_bond(nation_name, buy_value=static.STARTING_INVESTMENT)
            self.bonds_by_player_by_nation[player.id][nation_name].append(static.STARTING_INVESTMENT)
            # secondary investment
            secondary_nation_name = static.STARTING_NATION_SECOND_INVESTMENT[nation_name]
            self.nations[secondary_nation_name].transact_bond(value=static.SECONDARY_INVESTMENT)
            player.transact_bond(secondary_nation_name, buy_value=static.SECONDARY_INVESTMENT)
            self.bonds_by_player_by_nation[player.id][nation_name].append(static.SECONDARY_INVESTMENT)
            logger.info(f'Player {player.id} starts with {nation_name} and {secondary_nation_name}')
        self.update_nation_ownership()
        # determine who is left of Russia (or China) - they get the investor card
        if 'RUSSIA' in self.nation_to_player_map:
            player = self.nation_to_player_map['RUSSIA']
        else:
            player = self.nation_to_player_map['CHINA']
        self.next_investor_player_index = (self.players.index(player) + 1) % len(self.players)
        logger.info(f'Player {self.players[self.next_investor_player_index].id} will be first investor')

    def execute_command(self, command_string, first_command=False):
        player_id = self.nation_to_player_map[self.active_nation.name].id
        logger.info(f"Player {player_id} playing for {self.active_nation.name} commands: {command_string}")
        command_type = command_string.split(' ')[0]
        old_rondel_index = self.active_nation.rondel_index
        new_rondel_index = self._get_new_rondel_index(command_type)
        if not first_command:
            # make player pay for rondel movement
            cost = self.active_nation.get_rondel_move_cost()[new_rondel_index]
            if cost > 0:
                logger.info(f"Player {player_id} paid {cost} to advance to {command_type}")
            self.nation_to_player_map[self.active_nation.name].mutate_cash(-cost)
        self.active_nation.move_to_rondel_position(new_rondel_index)

        if command_type == 'Factory':
            if self.active_nation.cash >= static.FACTORY_COST:
                self.map.create_factory(command_string.split(' ')[1])
                self.active_nation.mutate_cash(-static.FACTORY_COST)
            else:
                print('Not enough cash to build a factory')
        elif command_type == 'Production':
            self.map.produce_units(self.active_nation.name)
        elif command_type == 'Maneuver':
            commands = self._extract_command_tuples(command_string)
            [self.map.attack(int(c[0]), c[1]) for c in commands]
        elif command_type == 'Investor':
            for player in self.players:
                interest = sum([static.BOND_VALUE_TO_INTEREST[v]
                                for v in self.bonds_by_player_by_nation[player.id][self.active_nation.name]])
                interest_paid = min(interest, self.active_nation.cash)
                player.mutate_cash(interest_paid)
                self.active_nation.mutate_cash(-interest_paid)
        elif command_type == 'Import':
            commands = self._extract_command_tuples(command_string)
            num_imports = min(static.MAX_IMPORT, self.active_nation.cash // static.IMPORT_COST_PER_UNIT)
            [self.map.create_unit(c[1], c[0], self.active_nation.name) for c in commands[:num_imports]]
            self.active_nation.mutate_cash(-num_imports * static.IMPORT_COST_PER_UNIT)
        elif command_type == 'Taxation':
            tax_val = self.active_nation.get_taxation_value()
            unit_cost = self.active_nation.get_unit_cost()
            self.active_nation.mutate_cash(max(tax_val - unit_cost, 0))
            power_points, bonus = self._tax_benefits(tax_val)
            self.active_nation.add_vp(power_points)
            self.nation_to_player_map[self.active_nation.name].mutate_cash(bonus)
        else:
            print(f'Unrecognized command {command_string}')

        if not first_command and new_rondel_index <= old_rondel_index:  # then we passed investor
            self.execute_investor()

    def execute_investor(self):
        investor_player = self.players[self.next_investor_player_index]
        self.next_investor_player_index = (self.next_investor_player_index + 1) % len(self.players)
        investor_player.mutate_cash(static.BEFORE_INVEST_BONUS)
        command = investor_player.decide_investment(self)
        nation = command.split(' ')[0]
        buy_value = int(command.split(' ')[1])
        sell_value = int(command.split(' ')[2])

        if buy_value > 0:
            self.nations[nation].transact_bond(buy_value, sell_value)
            investor_player.transact_bond(nation, buy_value, sell_value)
            logger.info(f"Player {investor_player.id} invests {buy_value} in {nation}, trades in {sell_value}")

            self.update_nation_ownership()

    def game_finished(self):
        for nation in self.nations.values():
            if nation.vp >= 25:
                return True
        return False

    def update_active_nation(self):
        l = static.NATION_TURN_LIST
        next_nation_name = l[(l.index(self.active_nation.name) + 1) % len(l)]
        self.active_nation = self.nations[next_nation_name]
        self.ply_count += 1

    def update_nation_ownership(self):
        for nation in self.nations:
            investment_levels = [(player, player.get_investment_in_nation(nation)) for player in self.players]
            investment_levels.sort(key=lambda x: -x[1])
            if investment_levels[0][1] > 0:
                if nation in self.nation_to_player_map and self.nation_to_player_map[nation] != investment_levels[0][0]:
                    logger.info(f"Power change {investment_levels[0][0].id} now controls {nation}, "
                                     f"previously {self.nation_to_player_map[nation].id}")
                self.nation_to_player_map[nation] = investment_levels[0][0]

    def _extract_command_tuples(self, command_string):
        command_type = command_string.split(' ')[0]
        return [(c.split(' ')[0], c.split(' ')[1]) for c in command_string[len(command_type) + 1:].split(', ')]

    def _tax_benefits(self, tax_value):
        power_points = self._get_bucket_value(tax_value, static.TAX_BENEFIT['buckets'], static.TAX_BENEFIT['power'])
        bonus = self._get_bucket_value(tax_value, static.TAX_BENEFIT['buckets'], static.TAX_BENEFIT['bonus'])
        return power_points, bonus

    def _get_bucket_value(self, value, bucket_bounds, bucket_values):
        for i in range(len(bucket_bounds)):
            if value < bucket_bounds[i]:
                return bucket_values[i]
        return bucket_values[-1]

    def _get_new_rondel_index(self, command_type):
        rondel_position_names = list(static.RONDEL_POSITIONS.values())
        try:
            new_index = rondel_position_names[self.active_nation.rondel_index:].index(command_type) \
                        + self.active_nation.rondel_index
        except ValueError:
            new_index = rondel_position_names.index(command_type)
        return new_index
