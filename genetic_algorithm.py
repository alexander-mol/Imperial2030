import random
import copy
import time
import _pickle

mutation_rate = 0.3
mutation_magnitude = 0.3
pop_size = 8
num_generations = 300


def mutate(dna, scale=None):
    if not scale:
        scale = {k: 1.0 for k in dna}
    for key, value in dna.items():
        if random.random() < mutation_rate:
            if isinstance(value, int):
                value += random.choice([-1, 1])
            elif scale:
                value += (2 * random.random() - 1) * mutation_magnitude * scale[key]
        dna[key] = value


def combine(dna1, dna2):
    dna_new = {}
    for key, value in dna1.items():
        if random.random() < 0.5:
            dna_new[key] = value
        else:
            dna_new[key] = dna2[key]
    return dna_new


def run_evolution(fitness_func, base_params, recalculate=False):
    t0 = time.time()
    pop = [(copy.copy(base_params), 0.0) for _ in range(pop_size)]  # individual = (dna, fitness)

    for ind in pop[1:]:
        for i in range(5):  # apply 5 rounds of mutation for starting dna
            mutate(ind[0], scale=base_params)

    mid_point = round(pop_size / 2)

    t = time.time()
    for gen_i in range(num_generations):

        # mutate
        for ind in pop[mid_point:]:
            mutate(ind[0])

        # fitness
        if recalculate:
            start = 0
        else:
            start = mid_point
        for i, ind in enumerate(pop[start:]):
            pop[start + i] = (ind[0], fitness_func(ind[0]))

        # sort
        pop.sort(key=lambda x: -x[1])

        # store results
        with open('pop_cache.p', 'wb') as f:
            _pickle.dump(pop, f)

        # generate new individuals
        for i in range(mid_point, len(pop)):
            father_i = random.randint(0, mid_point - 1)
            mother_i = random.randint(0, mid_point - 1)
            pop[i] = (combine(pop[father_i][0], pop[mother_i][0]), None)

        printable_fitness = {k: round(v, 3) for k, v in pop[0][0].items()}
        print(f'G{gen_i}, {time.time() - t:.0f}s, fitness = ({pop[0][1]}, {pop[mid_point-1][1]}) '
              f'using: {printable_fitness}')
        t = time.time()
    print(f'Finished in {t - t0:.2f} s')
