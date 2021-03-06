import logging
from data_loader import territories
from static import NATION_TURN_LIST

logger = logging.getLogger(__name__)


class Map:

    def __init__(self):
        self.territories = territories
        self.nation_home_territories = {n: self.get_nation_home_territories(n) for n in NATION_TURN_LIST}
        self.unit_directory = {}
        self.unit_ids_by_nation = {nation: [] for nation in NATION_TURN_LIST}
        self.unit_ids_by_territory = {territory: [] for territory in self.territories}
        self.next_unit_id = 0
        self.factory_directory = {}
        self.factory_ids_by_nation = {nation: [] for nation in NATION_TURN_LIST}
        self.factory_ids_by_territory = {territory: [] for territory in self.territories}
        self.next_factory_id = 0
        self.flags_by_nation = {nation: [] for nation in NATION_TURN_LIST}
        self.flags_by_territory = {t: None for t in self.territories}

    # TODO align use of location and territory
    # TODO handle peacefully entering locations (maybe add flag that gets reset) - difficult because intra-turn aspect
    # TODO implement killing factories

    def create_factory(self, location_name):
        location = self.territories[location_name]
        if location['industry'] is not 'NONE' and not self.factory_ids_by_territory[location_name]:
            self.factory_directory[self.next_factory_id] = \
                Factory(self.next_factory_id, location['industry'], location_name, location['nation'])
            self.factory_ids_by_territory[location_name].append(self.next_factory_id)
            self.factory_ids_by_nation[location['nation']].append(self.next_factory_id)
            self.next_factory_id += 1
        else:
            raise(f'Failed to create factory for {location}')

    def produce_units(self, nation):
        for factory_id in self.factory_ids_by_nation[nation]:
            factory_obj = self.factory_directory[factory_id]
            if factory_obj.active:
                self.create_unit(factory_obj.type, factory_obj.location, factory_obj.nation)

    def create_unit(self, type, location, nation):
        unit_obj = Unit(self.next_unit_id, type, location, nation)
        self.unit_directory[unit_obj.id] = unit_obj
        self.unit_ids_by_nation[nation].append(unit_obj.id)
        self.unit_ids_by_territory[location].append(unit_obj.id)
        self.next_unit_id += 1

    def move_along_path(self, unit_id, path):
        if self.unit_directory[unit_id].has_moved:
            raise(f'Tried to move unit {unit_id}, {self.unit_directory[unit_id]} but it was already moved this turn.')
        old_location = self.unit_directory[unit_id].location
        new_location = path[-1]
        self.unit_ids_by_territory[old_location].remove(unit_id)
        self.unit_ids_by_territory[new_location].append(unit_id)
        unit = self.unit_directory[unit_id]
        unit.location = new_location
        unit.has_moved = True
        self.update_flag(unit_id)
        if unit.type == 'TANK':
            for l in path:
                if self.territories[l]['type'] == 'WATER':
                    units = self.get_units_on_territory(l, nation=unit.nation)
                    found_host = False
                    for u in units:
                        if u.type == 'SHIP' and not u.has_transported:
                            u.has_transported = True
                            found_host = True
                            break
                    if not found_host:
                        raise(f'Moving unit id {unit_id} along path {path} there was no available host ship at {l}')
            # check for factory re-enabling
            factories_on_old_territory = self.get_factories_on_territory(old_location)
            if len(factories_on_old_territory) > 0:
                for factory in factories_on_old_territory:
                    if factory.nation != unit.nation:
                        disabling_units_on_territory = \
                            [u for u in self.get_units_on_territory(old_location) if u.nation != factory.nation]
                        if len(disabling_units_on_territory) == 0:
                            factory.active = True
                            logger.info(f'{factory} reactivated')

    def update_flag(self, unit_id):
        unit = self.unit_directory[unit_id]
        territory_name = unit.location
        if self.territories[territory_name]['nation'] == 'NONE':
            old_nation = self.flags_by_territory[territory_name]
            if old_nation:
                self.flags_by_nation[old_nation].remove(territory_name)
            self.flags_by_nation[unit.nation].append(territory_name)
            self.flags_by_territory[territory_name] = unit.nation

    def delete_unit(self, unit_id):
        territory = self.unit_directory[unit_id].location
        nation = self.unit_directory[unit_id].nation
        del self.unit_directory[unit_id]
        self.unit_ids_by_territory[territory].remove(unit_id)
        self.unit_ids_by_nation[nation].remove(unit_id)

    def get_units_of_nation(self, nation):
        return [self.unit_directory[unit_id] for unit_id in self.unit_ids_by_nation[nation]]

    def get_units_on_territory(self, territory_name, nation=None):
        units_on_territory = [self.unit_directory[unit_id] for unit_id in self.unit_ids_by_territory[territory_name]]
        if nation is None:
            return units_on_territory
        else:
            return [unit for unit in units_on_territory if unit.nation == nation]

    def get_factories_of_nation(self, nation):
        return [self.factory_directory[factory_id] for factory_id in self.factory_ids_by_nation[nation]]

    def get_factories_on_territory(self, territory_name):
        return [self.factory_directory[factory_id] for factory_id in self.factory_ids_by_territory[territory_name]]

    def get_flags_of_nation(self, nation):
        return self.flags_by_nation[nation]

    def refresh(self, nation):
        for unit_id in self.unit_ids_by_nation[nation]:
            self.unit_directory[unit_id].has_moved = False
            if self.unit_directory[unit_id] == 'SHIP':
                self.unit_directory[unit_id].has_transported = False
        # for factory_id in self.factory_ids_by_nation[nation]:
        #     factory_obj = self.factory_directory[factory_id]
        #     enemy_units_on_factory = \
        #         [u for u in self.get_units_on_territory(factory_obj.location) if u.nation != factory_obj.nation]
        #     if len(enemy_units_on_factory) > 0:
        #         if factory_obj.active:
        #             logger.warning(f"WARNING: factory {factory_obj} thought it was active but it shouldn't have been")
        #             factory_obj.active = False
        #     else:
        #         factory_obj.active = True

    def get_path(self, unit_id, target_location):
        if self.unit_directory[unit_id].type == 'SHIP':
            reachable_locations, shortest_paths = self.get_paths_ship(unit_id, target_location)
        else:
            reachable_locations, shortest_paths = self.get_paths_tank(unit_id, target_location)
        return None if target_location not in shortest_paths else shortest_paths[target_location]

    def get_paths(self, unit_id):
        if self.unit_directory[unit_id].type == 'SHIP':
            return self.get_paths_ship(unit_id)
        else:
            return self.get_paths_tank(unit_id)

    def get_paths_ship(self, unit_id, target_location=None):
        location = self.unit_directory[unit_id].location
        reachable_locations = [l for l in self.territories[location]['adjacency'] if territories[l]['type'] == 'WATER']
        if self.territories[location]['type'] == 'WATER':
            reachable_locations.append(location)
        shortest_paths = {l: [l] for l in reachable_locations}
        return reachable_locations, shortest_paths

    def get_paths_tank(self, unit_id, target_location=None):
        location = self.unit_directory[unit_id].location
        if location == target_location:
            return {target_location}, {target_location: [target_location]}
        nation = self.unit_directory[unit_id].nation
        seen_locations = {location}
        reachable_locations = [location]
        unexplored_locations = [location]
        shortest_paths = {location: [location]}
        if target_location is not None and territories[target_location]['type'] == 'WATER':
            logger.warning(f'WARNING: Cannot send a TANK ({unit_id}) to a WATER location ({target_location})')
            return reachable_locations, shortest_paths
        nation_home_territory_names = [t['name'] for t in self.nation_home_territories[nation]]
        trains_relevant = location in nation_home_territory_names and self._railroads_active(nation)
        while len(unexplored_locations) > 0:
            l0 = unexplored_locations.pop(0)
            for l1 in self.territories[l0]['adjacency']:
                if l1 in seen_locations:
                    continue
                elif self.territories[l1]['type'] == 'LAND':
                    reachable_locations.append(l1)
                    shortest_paths[l1] = shortest_paths[l0] + [l1]
                    if l1 == target_location:
                        return reachable_locations, shortest_paths
                    if trains_relevant and l1 in nation_home_territory_names:
                        unexplored_locations.append(l1)
                elif self.territories[l1]['type'] == 'WATER':
                    for unit in self.get_units_on_territory(l1, nation):
                        if unit.type == 'SHIP' and not unit.has_transported:
                            unexplored_locations.append(l1)
                            shortest_paths[l1] = shortest_paths[l0] + [l1]
                seen_locations.add(l1)

        return reachable_locations, shortest_paths

    def _railroads_active(self, nation):
        for t in self.nation_home_territories[nation]:
            if len([u for u in self.get_units_on_territory(t['name']) if u.nation != nation]) > 0:
                # TODO peacefully entering is not handled properly here
                return False
        return True

    def get_nation_home_territories(self, nation):
        return [t for t in self.territories.values() if t['nation'] == nation]

    def attack(self, unit_id, target_location, target_nation=None, target_factory=False):
        path = self.get_path(unit_id, target_location)
        if not path:
            logger.warning(f'WARNING: Unit id {unit_id} cannot attack {target_location}, no path')
            return
        unit = self.unit_directory[unit_id]
        target_units = [u for u in self.get_units_on_territory(target_location) if u.nation != unit.nation]
        if len(target_units) > 0:
            if target_nation is None:
                target_unit = target_units[0]
            else:
                try:
                    target_unit = [u for u in target_units if u.nation == target_nation][0]
                except:
                    raise(f'Tried to attack {target_nation} in {target_location} but no such units present')
            # handle killing
            self.delete_unit(unit_id)
            self.delete_unit(target_unit.id)
            logger.info(f"Unit {unit} attacked {target_unit}")
            return
        else:
            # just walk in
            self.move_along_path(unit_id, path)
        target_factories = [f for f in self.get_factories_on_territory(target_location) if f.nation != unit.nation]
        if len(target_factories) > 0:
            for factory in target_factories:
                if factory.active:
                    factory.active = False
                    logger.info(f"{factory} disabled by {unit}")


class Unit:

    def __init__(self, id, type, location, nation):
        self.id = id
        self.type = type
        self.location = location
        self.nation = nation
        self.has_moved = False
        if type == 'SHIP':
            self.has_transported = False

    def __repr__(self):
        return f"{self.type[0]}.{self.nation[:2]}{self.id}@{self.location}"


class Factory:

    def __init__(self, id, type, location, nation):
        self.id = id
        self.type = type
        self.location = location
        self.nation = nation
        self.active = True

    def __repr__(self):
        base_string = f"F({self.type[0]})@{self.location}"
        return base_string if self.active else f"{base_string}-DISABLED"
