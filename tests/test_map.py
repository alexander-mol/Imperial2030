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

        expected_result = "[S.US0@SAN_FRANCISCO, T.US1@CHICAGO, S.US2@SAN_FRANCISCO, T.US3@CHICAGO]"
        # print(self.sut.get_units_of_nation('USA'))
        assert str(self.sut.get_units_of_nation('USA')) == expected_result

    def test_get_path(self):
        self.sut.create_unit('TANK', 'LONDON', 'EUROPE')
        print(self.sut.get_path(0, 'NORTH_ATLANTIC'))
        assert self.sut.get_path(0, 'NORTH_ATLANTIC') is None
        print(self.sut.get_path(0, 'PARIS'))
        assert self.sut.get_path(0, 'PARIS') == ['LONDON', 'PARIS']
        print(self.sut.get_path(0, 'BEIJING'))
        assert self.sut.get_path(0, 'BEIJING') is None
        print(self.sut.get_path(0, 'PARIS'))
        self.sut.create_unit('SHIP', 'NORTH_ATLANTIC', 'EUROPE')
        self.sut.create_unit('SHIP', 'CARIBBEAN_SEA', 'EUROPE')
        self.sut.create_unit('SHIP', 'SOUTH_ATLANTIC', 'EUROPE')
        print(self.sut.get_path(0, 'ARGENTINA'))
        assert self.sut.get_path(0, 'ARGENTINA') == \
               ['LONDON', 'NORTH_ATLANTIC', 'CARIBBEAN_SEA', 'SOUTH_ATLANTIC', 'ARGENTINA']

    def test_move_with_path(self):
        self.sut.create_unit('TANK', 'LONDON', 'EUROPE')
        self.sut.create_unit('SHIP', 'NORTH_ATLANTIC', 'EUROPE')
        self.sut.create_unit('SHIP', 'CARIBBEAN_SEA', 'EUROPE')
        self.sut.create_unit('SHIP', 'SOUTH_ATLANTIC', 'EUROPE')

        self.sut.move_along_path(0, self.sut.get_path(0, 'ARGENTINA'))

        # print(self.sut.unit_directory)
        # print(self.sut.flags_by_territory)
        assert self.sut.unit_directory[0].location == 'ARGENTINA'
        assert self.sut.unit_directory[0].has_moved == True
        assert self.sut.unit_directory[1].has_transported
        assert self.sut.unit_directory[2].has_transported
        assert self.sut.unit_directory[3].has_transported
        assert self.sut.flags_by_territory['ARGENTINA'] == 'EUROPE'

    def test_move_with_path_to_original_location(self):
        self.sut.create_unit('TANK', 'AFGHANISTAN', 'USA')

        self.sut.move_along_path(0, self.sut.get_path(0, 'AFGHANISTAN'))
        assert self.sut.unit_directory[0].location == 'AFGHANISTAN'

        self.sut.create_unit('SHIP', 'NORTH_ATLANTIC', 'USA')
        self.sut.move_along_path(1, self.sut.get_path(1, 'NORTH_ATLANTIC'))
        assert self.sut.unit_directory[1].location == 'NORTH_ATLANTIC'

    def test_attack(self):
        self.sut.create_unit('TANK', 'NORTH_AFRICA', 'EUROPE')
        self.sut.create_unit('TANK', 'NORTH_AFRICA', 'EUROPE')
        self.sut.create_unit('TANK', 'NIGERIA', 'BRAZIL')
        self.sut.create_unit('TANK', 'NIGERIA', 'BRAZIL')

        self.sut.attack(0, 'NIGERIA')

        print(self.sut.unit_directory)
        assert str(self.sut.unit_directory) == "{1: T.EU1@NORTH_AFRICA, 3: T.BR3@NIGERIA}"

    def test_move_railroad(self):
        self.sut.create_unit('TANK', 'LONDON', 'EUROPE')
        assert self.sut._railroads_active('EUROPE')
        print(self.sut.get_path(0, 'TURKEY'))
        assert self.sut.get_path(0, 'TURKEY') == ['LONDON', 'PARIS', 'ROME', 'TURKEY']
        self.sut.create_unit('TANK', 'BERLIN', 'CHINA')
        assert not self.sut._railroads_active('EUROPE')
        assert self.sut.get_path(0, 'TURKEY') is None
        assert self.sut.get_path(0, 'ROME') is None
        assert self.sut.get_path(0, 'PARIS') == ['LONDON', 'PARIS']
        assert self.sut.get_path(1, 'TURKEY') is None

    def test_factory_disabling(self):
        # factory is available - move unit onto it - check if disabled - wait one turn - move unit off - check active
        self.sut.create_factory('SAN_FRANCISCO')
        self.sut.create_unit('TANK', 'NEW_ORLEANS', 'CHINA')
        assert self.sut.factory_directory[0].active
        self.sut.attack(0, 'SAN_FRANCISCO')
        assert not self.sut.factory_directory[0].active
        self.sut.refresh('USA')
        assert not self.sut.factory_directory[0].active
        self.sut.refresh('CHINA')
        self.sut.attack(0, 'CANADA')
        assert self.sut.factory_directory[0].active