import pandas as pd
import os
from path_config import ROOT_PATH

territories = pd.read_excel(os.path.join(ROOT_PATH, 'territories.xlsx')).to_dict('index')
for key in list(territories.keys()):
    territories[territories[key]['name']] = territories[key]
    territories[key]['adjacency'] = territories[key]['adjacency'].split(';')
    del territories[key]


# consistency checks

# country not contained in own adjacency list
for ter in territories:
    if ter in territories[ter]['adjacency']:
        print(f'{ter} in own adjacency list')

# rare occurrences - indicate misspellings
# occurrences = []
# for ter in territories:
#     occurrences += territories[ter]['adjacency']
# counts = {}
# for oc in occurrences:
#     if oc in counts:
#         counts[oc] += 1
#     else:
#         counts[oc] = 1
# print(sorted(list(counts.items()), key=lambda x: x[1])[:10])

# reciprocating relationships
for ter in territories:
    for adj in territories[ter]['adjacency']:
        if ter not in territories[adj]['adjacency']:
            print(f"{adj} missing {ter}")

# each adjacency item is spelled correctly
for ter in territories:
    for adj in territories[ter]['adjacency']:
        if adj not in territories:
            print(f'{adj} not found in territories')

# duplicates in adjacency list
for ter in territories:
    for adj in territories[ter]['adjacency']:
        i0 = territories[ter]['adjacency'].index(adj)
        i1 = territories[ter]['adjacency'][::-1].index(adj)
        if i0 + i1 + 1 != len(territories[ter]['adjacency']):
            print(f"{ter} has duplicate {territories[ter]['adjacency'][i0]}")


# interesting statistics
# import copy
# t_copy = copy.copy(list(territories.values()))
# for t in t_copy:
#     t['adj_c'] = len(t['adjacency'])
# t_copy.sort(key=lambda x: -x['adj_c'])
# for t in t_copy:
#     print(t)