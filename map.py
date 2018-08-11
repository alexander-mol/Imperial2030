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
        self.flags_by_territory = {t: None for t in self.territories}

    # TODO implement disabling factories
    # TODO align use of location and territory
    # TODO handle peacefully entering locations (maybe add flag that gets reset)
    # TODO implement killing factories
    # TODO transporting via ships should use optimal configuration

    def create_factory(self, location_name):
        location = self.territories[location_name]
        if location['industry'] is not 'NONE' and not self.factory_ids_by_territory[location_name]:
            self.factory_directory[self.next_factory_id] = {'industry': location['industry'],
                                                            'active': True, 'nation': location['nation'],
                                                            'location': location_name, 'id': self.next_factory_id}
            self.factory_ids_by_territory[location_name].append(self.next_factory_id)
            self.factory_ids_by_nation[location['nation']].append(self.next_factory_id)
            self.next_factory_id += 1
        else:
            raise(f'Failed to create factory for {location}')

    def produce_units(self, nation):
        # TODO active factory provision
        for factory_id in self.factory_ids_by_nation[nation]:
            factory_obj = self.factory_directory[factory_id]
            self.create_unit(factory_obj['location'], factory_obj['industry'], factory_obj['nation'])

    def create_unit(self, location, type, nation):
        unit_obj = {'type': type, 'location': location, 'nation': nation, 'has_moved': False, 'id': self.next_unit_id}
        if type == 'SHIP':
            unit_obj['has_transported'] = False
        self.unit_directory[self.next_unit_id] = unit_obj
        self.unit_ids_by_nation[nation].append(self.next_unit_id)
        self.unit_ids_by_territory[location].append(self.next_unit_id)
        self.next_unit_id += 1

    def move_unit_without_path_check(self, unit_id, target_location_name):
        if not self.unit_directory[unit_id]['has_moved']:
            self.unit_directory[unit_id]['location'] = target_location_name
            self.unit_directory[unit_id]['has_moved'] = True
        else:
            print(f'Tried to move unit {unit_id}, {self.unit_directory[unit_id]} but it was already moved this turn.')

    def move_along_path(self, unit_id, path):
        if self.unit_directory[unit_id]['has_moved']:
            raise(f'Tried to move unit {unit_id}, {self.unit_directory[unit_id]} but it was already moved this turn.')
        old_location = self.unit_directory[unit_id]['location']
        new_location = path[-1]
        self.unit_ids_by_territory[old_location].remove(unit_id)
        self.unit_ids_by_territory[new_location].append(unit_id)
        self.unit_directory[unit_id]['location'] = new_location
        self.unit_directory[unit_id]['has_moved'] = True
        self.update_flag(unit_id)
        if self.unit_directory[unit_id]['type'] == 'TANK':
            for l in path:
                if self.territories[l]['type'] == 'WATER':
                    units = self.get_units_on_territory(l, nation=self.unit_directory[unit_id]['nation'])
                    found_host = False
                    for u in units:
                        if u['type'] == 'SHIP' and not u['has_transported']:
                            u['has_transported'] = True
                            found_host = True
                            break
                    if not found_host:
                        raise(f'Moving unit id {unit_id} along path {path} there was no available host ship at {l}')

    def update_flag(self, unit_id):
        unit = self.unit_directory[unit_id]
        territory_name = unit['location']
        if self.territories[territory_name]['nation'] == 'NONE':
            self.flags_by_territory[territory_name] = unit['nation']

    def delete_unit(self, unit_id):
        territory = self.unit_directory[unit_id]['location']
        nation = self.unit_directory[unit_id]['nation']
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
            return [unit for unit in units_on_territory if unit['nation'] is nation]

    def get_factories_of_nation(self, nation):
        return [self.factory_directory[factory_id] for factory_id in self.factory_ids_by_nation[nation]]

    def get_factories_on_territory(self, territory_name):
        return [self.factory_directory[factory_id] for factory_id in self.factory_ids_by_territory[territory_name]]

    def get_flags_of_nation(self, nation):
        # TODO can be optimized by keeping a list of flags by nation
        return [territory for territory, owner_nation in self.flags_by_territory.items() if owner_nation == nation]

    def refresh_units(self, nation):
        for unit_id in self.unit_ids_by_nation[nation]:
            self.unit_directory[unit_id]['has_moved'] = False
            if self.unit_directory[unit_id] == 'SHIP':
                self.unit_directory[unit_id]['has_transported'] = False

    def get_path(self, unit_id, target_location):
        if self.unit_directory[unit_id]['type'] == 'SHIP':
            reachable_locations, shortest_paths = self.get_paths_ship(unit_id, target_location)
            return shortest_paths[target_location]
        else:
            reachable_locations, shortest_paths = self.get_paths_tank(unit_id, target_location)
            return shortest_paths[target_location]

    def get_paths(self, unit_id):
        if self.unit_directory[unit_id]['type'] == 'SHIP':
            return self.get_paths_ship(unit_id)
        else:
            return self.get_paths_tank(unit_id)

    def get_paths_ship(self, unit_id, target_location=None):
        location = self.unit_directory[unit_id]['location']
        reachable_locations = [l for l in self.territories[location]['adjacency'] if territories[l]['type'] == 'WATER']
        if self.territories[location]['type'] == 'WATER':
            reachable_locations.append(location)
        shortest_paths = {target_location: None}
        shortest_paths.update({l: [l] for l in reachable_locations})
        return reachable_locations, shortest_paths

    def get_paths_tank(self, unit_id, target_location=None):
        location = self.unit_directory[unit_id]['location']
        if location == target_location:
            return {target_location}, {target_location: [target_location]}
        nation = self.unit_directory[unit_id]['nation']
        seen_locations = {location}
        reachable_locations = [location]
        unexplored_locations = [location]
        shortest_paths = {location: [location], target_location: None}
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
                    shortest_paths[l1] = shortest_paths[l0] + [l1]
                    return reachable_locations, shortest_paths
                if trains_relevant and l1 in nation_home_territory_names:
                    reachable_locations.append(l1)
                    unexplored_locations.append(l1)
                    shortest_paths[l1] = shortest_paths[l0] + [l1]
                elif self.territories[l1]['type'] == 'WATER':
                    for unit in self.get_units_on_territory(l1, nation):
                        if unit['type'] == 'SHIP' and not unit['has_transported']:
                            unexplored_locations.append(l1)
                            shortest_paths[l1] = shortest_paths[l0] + [l1]
                seen_locations.add(l1)

        return reachable_locations, shortest_paths

    def _railroads_active(self, nation):
        for t in self.nation_home_territories[nation]:
            if len([u for u in self.get_units_on_territory(t['name']) if u['nation'] != nation]) > 0:
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
        target_units = [u for u in self.get_units_on_territory(target_location) if u['nation'] != unit['nation']]
        if len(target_units) > 0:
            if target_nation is None:
                target_unit = target_units[0]
            else:
                try:
                    target_unit = [u for u in target_units if u['nation'] == target_nation][0]
                except:
                    raise(f'Tried to attack {target_nation} in {target_location} but no such units present')
            # handle killing
            self.delete_unit(unit_id)
            self.delete_unit(target_unit['id'])
            logger.info(f"Unit {unit_id} attacked {target_unit['id']}")
        else:
            # just walk in
            self.move_along_path(unit_id, path)
