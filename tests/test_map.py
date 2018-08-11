import unittest
import map


class TestMap(unittest.TestCase):

    def setUp(self):
        self.sut = map.Map()


    def test_produce_units(self):
        self.sut.create_factory('SAN_FRANCISCO')
        self.sut.create_factory('CHICAGO')
        self.sut.create_factory('LONDON')
        self.sut.produce_units('USA')
        self.sut.produce_units('USA')

        expected_result = [{'type': 'SHIP', 'location': 'SAN_FRANCISCO', 'nation': 'USA', 'has_moved': False, 'id': 0, 'has_transported': False}, {'type': 'TANK', 'location': 'CHICAGO', 'nation': 'USA', 'has_moved': False, 'id': 1}, {'type': 'SHIP', 'location': 'SAN_FRANCISCO', 'nation': 'USA', 'has_moved': False, 'id': 2, 'has_transported': False}, {'type': 'TANK', 'location': 'CHICAGO', 'nation': 'USA', 'has_moved': False, 'id': 3}]
        # print(self.sut.get_units_of_nation('USA'))
        assert self.sut.get_units_of_nation('USA') == expected_result

    def test_get_path(self):
        self.sut.create_unit('LONDON', 'TANK', 'EUROPE')
        print(self.sut.get_path(0, 'NORTH_ATLANTIC'))
        assert self.sut.get_path(0, 'NORTH_ATLANTIC') is None
        print(self.sut.get_path(0, 'PARIS'))
        assert self.sut.get_path(0, 'PARIS') == ['LONDON', 'PARIS']
        print(self.sut.get_path(0, 'BEIJING'))
        assert self.sut.get_path(0, 'BEIJING') is None
        print(self.sut.get_path(0, 'PARIS'))
        self.sut.create_unit('NORTH_ATLANTIC', 'SHIP', 'EUROPE')
        self.sut.create_unit('CARIBBEAN_SEA', 'SHIP', 'EUROPE')
        self.sut.create_unit('SOUTH_ATLANTIC', 'SHIP', 'EUROPE')
        print(self.sut.get_path(0, 'ARGENTINA'))
        # print(self.sut.get_path(0, 'ARGENTINA'))
        assert self.sut.get_path(0, 'ARGENTINA') == \
               ['LONDON', 'NORTH_ATLANTIC', 'CARIBBEAN_SEA', 'SOUTH_ATLANTIC', 'ARGENTINA']

    def test_move_with_path(self):
        self.sut.create_unit('LONDON', 'TANK', 'EUROPE')
        self.sut.create_unit('NORTH_ATLANTIC', 'SHIP', 'EUROPE')
        self.sut.create_unit('CARIBBEAN_SEA', 'SHIP', 'EUROPE')
        self.sut.create_unit('SOUTH_ATLANTIC', 'SHIP', 'EUROPE')

        self.sut.move_along_path(0, self.sut.get_path(0, 'ARGENTINA'))

        # print(self.sut.unit_directory)
        # print(self.sut.flags_by_territory)
        assert self.sut.unit_directory[0]['location'] == 'ARGENTINA'
        assert self.sut.unit_directory[0]['has_moved'] == True
        assert self.sut.unit_directory[1]['has_transported']
        assert self.sut.unit_directory[2]['has_transported']
        assert self.sut.unit_directory[3]['has_transported']
        assert self.sut.flags_by_territory['ARGENTINA'] == 'EUROPE'

    def test_move_with_path_to_original_location(self):
        self.sut.create_unit('AFGHANISTAN', 'TANK', 'USA')

        self.sut.move_along_path(0, self.sut.get_path(0, 'AFGHANISTAN'))
        assert self.sut.unit_directory[0]['location'] == 'AFGHANISTAN'

        self.sut.create_unit('NORTH_ATLANTIC', 'SHIP', 'USA')
        self.sut.move_along_path(1, self.sut.get_path(1, 'NORTH_ATLANTIC'))
        assert self.sut.unit_directory[1]['location'] == 'NORTH_ATLANTIC'

    def test_attack(self):
        self.sut.create_unit('NORTH_AFRICA', 'TANK', 'EUROPE')
        self.sut.create_unit('NORTH_AFRICA', 'TANK', 'EUROPE')
        self.sut.create_unit('NIGERIA', 'TANK', 'BRAZIL')
        self.sut.create_unit('NIGERIA', 'TANK', 'BRAZIL')

        self.sut.attack(0, 'NIGERIA')

        # print(self.sut.unit_directory)
        assert self.sut.unit_directory == {1: {'type': 'TANK', 'location': 'NORTH_AFRICA', 'nation': 'EUROPE', 'has_moved': False, 'id': 1}, 3: {'type': 'TANK', 'location': 'NIGERIA', 'nation': 'BRAZIL', 'has_moved': False, 'id': 3}}

    def test_move_railroad(self):
        self.sut.create_unit('LONDON', 'TANK', 'EUROPE')
        assert self.sut._railroads_active('EUROPE')
        print(self.sut.get_path(0, 'TURKEY'))
        assert self.sut.get_path(0, 'TURKEY') == ['LONDON', 'PARIS', 'ROME', 'TURKEY']
        self.sut.create_unit('BERLIN', 'TANK', 'CHINA')
        assert not self.sut._railroads_active('EUROPE')
        assert self.sut.get_path(0, 'TURKEY') is None
        assert self.sut.get_path(0, 'ROME') is None
        assert self.sut.get_path(0, 'PARIS') == ['LONDON', 'PARIS']
        assert self.sut.get_path(1, 'TURKEY') is None
