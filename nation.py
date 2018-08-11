import static


class Nation:

    def __init__(self, name, map):
        self.name = name
        self.map = map
        self.rondel_index = -1
        self.cash = 0
        self.vp = 0
        self.bonds = \
            [{'interest': i, 'value': v, 'nation': self.name} for v, i in static.BOND_VALUE_TO_INTEREST.items()]

    def mutate_cash(self, amount):
        self.cash += amount

    def get_taxation_value(self):
        # TODO handle disabled factories properly here
        active_factories = [f for f in self.map.get_factories_of_nation(self.name) if f['active']]
        flags = self.map.get_flags_of_nation(self.name)
        return 2 * len(active_factories) + len(flags)

    def get_unit_cost(self):
        return len(self.map.get_units_of_nation(self.name)) * static.TAXATION_COST_PER_UNIT

    def add_vp(self, points):
        self.vp += points

    @property
    def vp_class(self):
        return self.vp // 5

    def move_to_rondel_position(self, rondel_position_int):
        self.rondel_index = rondel_position_int

    def get_rondel_move_cost(self):
        output = {}
        for i in range(1, len(static.RONDEL_POSITIONS) + 1):
            true_position = (self.rondel_index + i) % len(static.RONDEL_POSITIONS)
            if i <= 3:
                output[true_position] = 0
            else:
                output[true_position] = (self.vp_class + 1) * (i - 3)
        return output

    def transact_bond(self, value, trade_in_value=None):
        sold_bond = None
        for i, bond in enumerate(self.bonds):
            if bond['value'] == value:
                sold_bond = self.bonds.pop(i)
                break
        if trade_in_value:
            self.bonds.append(
                {'nation': self.name,
                 'value': trade_in_value,
                 'interest': static.BOND_VALUE_TO_INTEREST[trade_in_value]})
            self.mutate_cash(value - trade_in_value)
        else:
            self.mutate_cash(value)
        return sold_bond

    def get_units(self):
        return self.map.get_units_of_nation(self.name)

    def get_flags(self):
        return self.map.get_flags_of_nation(self.name)

    def get_factories(self):
        return self.map.get_factories_of_nation(self.name)

    def get_home_territories(self):
        return self.map.get_nation_home_territories(self.name)
