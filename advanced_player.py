import base_player
import math
import networkx as nx
import static


class SmartInvestor(base_player.BasePlayer):

    def __init__(self, id, dna):
        super().__init__(id)
        self.dna = dna

    def decide_investment(self, game):
        nation_value = []
        for nation in game.nations.values():
            nation_power_score = self._get_nation_power(game, nation)
            buy_value, sell_value = self._get_max_investment(nation)
            nation_value.append((nation, nation_power_score, buy_value, sell_value))
        nation_value.sort(key=lambda x: -x[1])
        invest_nation = nation_value[0][0].name
        buy_value = nation_value[0][2]
        sell_value = nation_value[0][3]
        return self._generate_command_invest(invest_nation, buy_value, sell_value)

    def get_turn_command(self, game):
        current_rondel_index = game.active_nation.rondel_index
        if current_rondel_index == 0:  # i.e. just before "Import"
            current_rondel_index += 1
        if current_rondel_index == 1:  # i.e. just before first "Production"
            if len(game.active_nation.get_units()) > len(game.active_nation.get_flags()) + 6:
                current_rondel_index += 1
        if current_rondel_index == 2: # i.e. just before first Maneuver
            if len(game.active_nation.get_units()) == 0:
                current_rondel_index += 1
        if current_rondel_index == 3: # i.e. just before "Taxation"
            if game.active_nation.get_taxation_value() < static.TAX_BENEFIT['buckets'][0]:
                current_rondel_index += 1
        if current_rondel_index == 4: # i.e. just before "Factory"
            if len(game.active_nation.get_factories()) == len(game.active_nation.get_home_territories()) or \
                    game.active_nation.cash < static.FACTORY_COST:
                current_rondel_index += 1
        if current_rondel_index == 5:  # i.e. just before second "Production"
            if len(game.active_nation.get_units()) > len(game.active_nation.get_flags()) + 6:
                current_rondel_index += 1
        if current_rondel_index == 6: # i.e. just before second Maneuver
            if len(game.active_nation.get_units()) == 0:
                current_rondel_index += 1

        command = static.RONDEL_POSITIONS[(current_rondel_index + 1) % len(static.RONDEL_POSITIONS)]
        if command == 'Factory':
            return self._generate_command_factory(self._decide_factory_build_location(game))

        elif command == 'Maneuver':
            return self._get_maneuver_commands(game)
        else:
            return command

    def _get_maneuver_commands(self, game):
        rooting_nations = self._get_rooting_nations(game)
        unit_ids = [u.id for u in game.active_nation.get_units()]
        g = nx.Graph()
        g.add_nodes_from(unit_ids)
        target_locations = []
        for unit_id in unit_ids:
            reachable_locations, shortest_paths = game.map.get_paths(unit_id)
            for location in reachable_locations:
                # if it is a neutral territory with a flag that isn't ours - add to target locations
                # ADDED PROVISION only if it doesn't harm our rooting_nations
                if game.map.territories[location]['nation'] == 'NONE' and \
                        game.map.flags_by_territory[location] != game.active_nation.name and \
                        game.map.flags_by_territory[location] not in rooting_nations:
                    target_locations.append(location)
                    g.add_node(location)
                    g.add_edge(unit_id, location)
                # or get an enemy factory
                enemy_factories = \
                    [f for f in game.map.get_factories_on_territory(location) if f.nation != game.active_nation.name and
                     f.nation not in rooting_nations]
                if len(enemy_factories) > 0:
                    for factory in enemy_factories:
                        target_locations.append(location)
                        g.add_node(location)
                        g.add_edge(unit_id, location)
                # alternatively if there's an enemy in our lands go for that too
                elif location in game.map.nation_home_territories[game.active_nation.name]:
                    unit_nations = [u.nation for u in game.map.get_units_on_territory(location)]
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
                        options.append((location, len(game.map.territories[location]['adjacency'])))
                if len(options) > 0:
                    options.sort(key=lambda x: -x[1])
                    assignments.update({unit_id: options[0][0]})
        # make sure tanks go first, then ships
        assignment_list = \
            sorted(list(assignments.items()), key=lambda x: 0 if game.map.unit_directory[x[0]].type == 'TANK' else 1)
        return self._generate_command_maneuver(assignment_list)

    def _get_rooting_nations(self, game):
        interest_points_by_nation = list(self.get_interest_by_nation(game).items())
        interest_points_by_nation.sort(key=lambda x: -x[1])
        rooting_nations = []
        for i in range(2):
            if interest_points_by_nation[i][1] > 0:
                rooting_nations.append(interest_points_by_nation[i][0])
        return rooting_nations

    def _get_nation_power(self, game, nation):
        ply_count_x = (game.ply_count - self.dna['ply_count_offset']) / self.dna['ply_count_weight']
        game_progression = self._sigmoid(ply_count_x)
        return nation.vp * self.dna['vp_weight'] * game_progression \
               + (len(nation.get_units()) * self.dna['num_units_weight']
               + nation.get_taxation_value() * self.dna['tax_val_weight']
               + nation.cash * self.dna['cash_weight']
               + self.dna[nation.name]) * (1 - game_progression)

    def _sigmoid(self, x):
        return math.exp(x) / (1 + math.exp(x))