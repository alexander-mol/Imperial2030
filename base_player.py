# methods needed
# rondel starting position
# turn method that generates a command list
# investment decision method

# for later:
# method to ask for allowed movement through a canal owned by the player

import random
import static
import networkx as nx


# TODO handle transporting second tank by ship - but not possible
# TODO make bond transacting nicer

class BasePlayer:

    def __init__(self, id):
        self.id = id
        self.cash = 0
        self.investments_by_nation = {n: [] for n in static.NATION_TURN_LIST}

    def get_initial_command(self, game):
        if game.active_nation.cash >= static.FACTORY_COST:
            return self._generate_command_factory(self._decide_factory_build_location(game))
        else:
            return self._generate_command_production()

    def get_turn_command(self, game):
        current_rondel_index = game.active_nation.rondel_index
        if current_rondel_index == 0:  # i.e. just before "Import"
            current_rondel_index += 1
        if current_rondel_index == 3: # i.e. just before "Taxation"
            if game.active_nation.get_taxation_value() < static.TAX_BENEFIT['buckets'][0]:
                current_rondel_index += 1
        if current_rondel_index == 4: # i.e. just before "Factory"
            if len(game.active_nation.get_factories()) == len(game.active_nation.get_home_territories()) or \
                    game.active_nation.cash < static.FACTORY_COST:
                current_rondel_index += 1

        command = static.RONDEL_POSITIONS[(current_rondel_index + 1) % len(static.RONDEL_POSITIONS)]
        if command == 'Factory':
            return self._generate_command_factory(self._decide_factory_build_location(game))

        elif command == 'Maneuver':
            return self._get_maneuver_commands(game)
        else:
            return command

    def decide_investment(self, game):
        nation_value = []
        for nation in game.nations.values():
            nation_power_score = nation.vp + nation.get_taxation_value()
            buy_value, sell_value = self._get_max_investment(nation)
            nation_value.append((nation, nation_power_score * (buy_value - sell_value), buy_value, sell_value))
        nation_value.sort(key=lambda x: -x[1])
        invest_nation = nation_value[0][0].name
        buy_value = nation_value[0][2]
        sell_value = nation_value[0][3]
        return self._generate_command_invest(invest_nation, buy_value, sell_value)

    def _get_maneuver_commands(self, game):
        unit_ids = [u['id'] for u in game.active_nation.get_units()]
        g = nx.Graph()
        g.add_nodes_from(unit_ids)
        target_locations = []
        for unit_id in unit_ids:
            reachable_locations, shortest_paths = game.map.get_paths(unit_id)
            for location in reachable_locations:
                # if it is a neutral territory with a flag that isn't ours - add to target locations
                if game.map.territories[location]['nation'] == 'NONE' and \
                        game.map.flags_by_territory[location] != game.active_nation.name:
                    target_locations.append(location)
                    g.add_node(location)
                    g.add_edge(unit_id, location)
                # alternatively if there's an enemy in our lands go for that too
                elif location in game.map.nation_home_territories[game.active_nation.name]:
                    unit_nations = [u['nation'] for u in game.map.get_units_on_territory(location)]
                    if len(unit_nations) > 0 and game.active_nation.name not in unit_nations:
                        target_locations.append(location)
                        g.add_node(location)
                        g.add_edge(unit_id, location)
        # find the maximum matching between tanks and target locations
        # all unassigned tanks get randomly assigned to things in target_locations that they can reach
        assignments = self.get_maximal_assignment(set(unit_ids), g, {})
        for unit_id in unit_ids:
            if unit_id not in assignments:
                # some units will have nothing reachable in target locations - randomly move to best connected space
                options = []
                reachable_locations, _ = game.map.get_paths(unit_id)
                for location in reachable_locations:
                    if location not in game.active_nation.get_home_territories():
                        options.append((location, len(reachable_locations)))
                if len(options) > 0:
                    options.sort(key=lambda x: -x[1])
                    assignments.update({unit_id: options[0][0]})
        return self._generate_command_maneuver(assignments)

    def get_maximal_assignment(self, unit_ids, g, assignments):
        current_assignments = nx.max_weight_matching(g, maxcardinality=True)
        if len(current_assignments) == 0:
            return assignments
        for key in list(current_assignments):
            if key not in unit_ids:
                del current_assignments[key]
            else:
                g.remove_node(key)
        assignments.update(current_assignments)
        return self.get_maximal_assignment(unit_ids, g, assignments)

    def _decide_factory_build_location(self, game):
        home_territories = [t['name'] for t in game.active_nation.get_home_territories()]
        factory_locations = [f['location'] for f in game.active_nation.get_factories()]
        return random.choice([x for x in home_territories if x not in factory_locations])

    def mutate_cash(self, amount):
        self.cash += amount

    def transact_bond(self, nation, buy_value, sell_value=0):
        if sell_value:
            bond_to_remove = None
            for b in self.investments_by_nation[nation]:
                if b['value'] == sell_value:
                    bond_to_remove = b
            self.investments_by_nation[nation].remove(bond_to_remove)
        self.investments_by_nation[nation].append(
            {'nation': nation, 'value': buy_value, 'interest': static.BOND_VALUE_TO_INTEREST[buy_value]}
        )
        self.mutate_cash(sell_value - buy_value)

    def get_current_vp(self, game):
        vp = self.cash
        for n, investments in self.investments_by_nation.items():
            vp += game.nations[n].vp_class * sum([investment['interest'] for investment in investments])
        return vp

    def _get_max_investment(self, nation):
        available_bond_values = [b['value'] for b in nation.bonds]
        owned_bond_values = [b['value'] for b in self.investments_by_nation[nation.name]]
        max_investment_without_trade_in = max([x for x in available_bond_values if x <= self.cash] + [0])
        trade_in_opportunities = \
            [(x, y, x - y) for x in available_bond_values for y in owned_bond_values if x - y <= self.cash]
        trade_in_opportunities.sort(key=lambda x: -x[2])
        if len(trade_in_opportunities) > 0:
            max_investment_with_trade_in = trade_in_opportunities[0][2]
            buy_value = trade_in_opportunities[0][0]
            sell_value = trade_in_opportunities[0][1]
            if max_investment_with_trade_in > max_investment_without_trade_in:
                return buy_value, sell_value
        return max_investment_without_trade_in, 0

    def get_investment_in_nation(self, nation):
        return sum([b['value'] for b in self.investments_by_nation[nation]])

    def _generate_command_factory(self, location):
        return f'Factory {location}'

    def _generate_command_production(self):
        return 'Production'

    def _generate_command_maneuver(self, unit_id_to_target_location_dict):
        return 'Maneuver ' + ', '.join([f'{u_id} {tl}' for u_id, tl in unit_id_to_target_location_dict.items()])

    def _generate_command_investor(self):
        return 'Investor'

    def _generate_command_import(self, location_to_type_dict):
        return 'Import' + ', '.join([f'{l} {t}' for l, t in location_to_type_dict.items()])

    def _generate_command_taxation(self):
        return 'Taxation'

    def _generate_command_invest(self, nation, buy, sell):
        return f'{nation} {buy} {sell}'
