############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: pyCombinatorial - Hybrid Genetic Search for the TSP
#
# GitHub Repository: <https://github.com/Valdecy>
#
# Notes:
#   This is a TSP-oriented Python adaptation of the general Hybrid Genetic
#   Search idea: population management with diversity control, ordered
#   crossover, mutation/perturbation, and local improvement. It is not a
#   direct CVRP port: the CVRP Split procedure, capacity penalties, duration
#   penalties, routes, and SWAP* inter-route neighborhood are intentionally
#   removed because a TSP solution is a single Hamiltonian cycle.
#
# Algorithm inspired by:
#   Vidal, T., Crainic, T. G., Gendreau, M., Lahrichi, N., Rei, W. (2012).
#   A hybrid genetic algorithm for multidepot and periodic vehicle routing
#   problems. Operations Research, 60(3), 611-624.
#
#   Vidal, T. (2022). Hybrid genetic search for the CVRP: Open-source
#   implementation and SWAP* neighborhood. Computers & Operations Research,
#   140, 105643.
#
############################################################################

# Required Libraries
import time
import random
import numpy as np

############################################################################

# Function: Tour Distance (same output convention as pyCombinatorial)
def distance_calc(distance_matrix, city_tour):
    distance = 0
    for k in range(0, len(city_tour[0]) - 1):
        m        = k + 1
        distance = distance + distance_matrix[city_tour[0][k] - 1, city_tour[0][m] - 1]
    return distance

############################################################################

# Function: Internal Closed-Tour Cost
def _route_cost(distance_matrix, route):
    n        = len(route)
    distance = 0.0
    for i in range(0, n):
        distance = distance + distance_matrix[route[i], route[(i + 1) % n]]
    return float(distance)

############################################################################

# Function: Convert Internal Route to pyCombinatorial City Tour
def _to_city_tour(distance_matrix, route):
    city_route = [int(i + 1) for i in route]
    city_route.append(city_route[0])
    distance   = distance_calc(distance_matrix, [city_route, 0])
    return [city_route, distance]

############################################################################

# Function: Matrix Check
def _prepare_distance_matrix(distance_matrix):
    distance_matrix = np.asarray(distance_matrix, dtype = float)
    if (distance_matrix.ndim != 2 or distance_matrix.shape[0] != distance_matrix.shape[1]):
        raise ValueError('distance_matrix must be a square matrix.')
    if (distance_matrix.shape[0] < 3):
        raise ValueError('TSP requires at least three cities.')
    if (not np.all(np.isfinite(distance_matrix))):
        raise ValueError('distance_matrix must contain only finite values.')
    return distance_matrix

############################################################################

# Function: Symmetry Check
def _is_symmetric(distance_matrix, atol = 1e-10):
    return bool(np.allclose(distance_matrix, distance_matrix.T, atol = atol, rtol = 0.0))

############################################################################

# Function: Nearest Candidate Lists
def _candidate_lists(distance_matrix, candidates):
    n          = distance_matrix.shape[0]
    candidates = int(max(1, min(candidates, n - 1)))
    cand       = []
    for i in range(0, n):
        row    = distance_matrix[i].copy()
        row[i] = np.inf
        cand.append(np.argsort(row, kind = 'stable')[:candidates].tolist())
    return cand

############################################################################

# Function: Tour Edges for Diversity Evaluation
def _edge_set(route, symmetric):
    n     = len(route)
    edges = set()
    for i in range(0, n):
        a = route[i]
        b = route[(i + 1) % n]
        if (symmetric == True and a > b):
            a, b = b, a
        edges.add((a, b))
    return edges

############################################################################

# Function: Broken-Pairs Distance
def _broken_pairs_distance(edges_a, edges_b, n):
    common = len(edges_a.intersection(edges_b))
    return 1.0 - common / float(n)

############################################################################

# Function: Average Distance to Closest Individuals
def _average_distance_to_closest(individual, population, closest):
    if (len(population) <= 1):
        return 1.0
    distances = []
    n         = len(individual['route'])
    for other in population:
        if (other is individual):
            continue
        distances.append(_broken_pairs_distance(individual['edges'], other['edges'], n))
    distances.sort()
    k = min(int(closest), len(distances))
    if (k <= 0):
        return 1.0
    return float(sum(distances[:k]) / k)

############################################################################

# Function: Build Individual
def _make_individual(distance_matrix, route, symmetric):
    route = list(route)
    return {
        'route'  : route,
        'cost'   : _route_cost(distance_matrix, route),
        'edges'  : _edge_set(route, symmetric),
        'fitness': 0.0,
    }

############################################################################

# Function: Normalize Route for Stable Representation
def _normalize_route(route):
    route = list(route)
    if (0 in route):
        p     = route.index(0)
        route = route[p:] + route[:p]
    return route

############################################################################

# Function: Random Route
def _random_route(n, rng):
    route = list(range(0, n))
    rng.shuffle(route)
    return _normalize_route(route)

############################################################################

# Function: Randomized Nearest Neighbor Route
def _randomized_nearest_neighbor(distance_matrix, rng, restricted_candidate_list = 3):
    n          = distance_matrix.shape[0]
    start      = rng.randrange(n)
    unvisited  = set(range(0, n))
    unvisited.remove(start)
    route      = [start]
    current    = start
    rcl_size   = max(1, int(restricted_candidate_list))
    while (len(unvisited) > 0):
        ranked = sorted(unvisited, key = lambda j: distance_matrix[current, j])
        limit  = min(rcl_size, len(ranked))
        nxt    = ranked[rng.randrange(limit)]
        route.append(nxt)
        unvisited.remove(nxt)
        current = nxt
    return _normalize_route(route)

############################################################################

# Function: Ordered Crossover (OX)
def _ordered_crossover(parent_a, parent_b, rng):
    n = len(parent_a)
    i = rng.randrange(0, n)
    j = rng.randrange(0, n)
    while (i == j):
        j = rng.randrange(0, n)
    if (i > j):
        i, j = j, i
    child          = [-1] * n
    child[i:j + 1] = parent_a[i:j + 1]
    used           = set(child[i:j + 1])
    fill_pos       = (j + 1) % n
    scan_pos       = (j + 1) % n
    for _ in range(0, n):
        city = parent_b[scan_pos]
        if (city not in used):
            child[fill_pos] = city
            fill_pos        = (fill_pos + 1) % n
            used.add(city)
        scan_pos = (scan_pos + 1) % n
    return _normalize_route(child)

############################################################################

# Function: Swap Mutation
def _swap_mutation(route, rng):
    n     = len(route)
    route = list(route)
    i, j  = rng.sample(range(0, n), 2)
    route[i], route[j] = route[j], route[i]
    return _normalize_route(route)

############################################################################

# Function: Double-Bridge Perturbation
def _double_bridge(route, rng):
    n = len(route)
    if (n < 8):
        return _swap_mutation(route, rng)
    cuts = sorted(rng.sample(range(1, n), 4))
    a, b, c, d = cuts
    new_route = route[0:a] + route[c:d] + route[b:c] + route[a:b] + route[d:n]
    return _normalize_route(new_route)

############################################################################

# Function: 2-Opt Local Search with Candidate Lists
def _two_opt_local_search(distance_matrix, route, candidate, max_passes = 50):
    n         = len(route)
    route     = list(route)
    best_cost = _route_cost(distance_matrix, route)
    eps       = 1e-12
    passes    = 0
    improved  = True
    while (improved == True and passes < max_passes):
        improved = False
        passes   = passes + 1
        pos      = [0] * n
        for idx, city in enumerate(route):
            pos[city] = idx
        for i in range(0, n - 1):
            a = route[i]
            b = route[(i + 1) % n]
            for c in candidate[a]:
                j = pos[c]
                if (j <= i + 1):
                    continue
                if (i == 0 and j == n - 1):
                    continue
                d     = route[(j + 1) % n]
                delta = (distance_matrix[a, c] + distance_matrix[b, d]
                         - distance_matrix[a, b] - distance_matrix[c, d])
                if (delta < -eps):
                    route[i + 1:j + 1] = reversed(route[i + 1:j + 1])
                    best_cost          = best_cost + float(delta)
                    improved           = True
                    break
            if (improved == True):
                break
    return _normalize_route(route), float(best_cost)

############################################################################

# Function: Update Biased Fitness
def _update_biased_fitness(population, elite, closest):
    if (len(population) == 0):
        return
    population.sort(key = lambda ind: ind['cost'])
    n_pop = len(population)
    if (n_pop == 1):
        population[0]['fitness'] = 0.0
        return

    diversity = []
    for ind in population:
        diversity.append(_average_distance_to_closest(ind, population, closest))

    cost_order = sorted(range(0, n_pop), key = lambda i: population[i]['cost'])
    div_order  = sorted(range(0, n_pop), key = lambda i: diversity[i], reverse = True)

    cost_rank = [0] * n_pop
    div_rank  = [0] * n_pop

    for r, idx in enumerate(cost_order):
        cost_rank[idx] = r
    for r, idx in enumerate(div_order):
        div_rank[idx] = r

    elite = max(1, min(int(elite), n_pop))
    for i in range(0, n_pop):
        fit_rank = cost_rank[i] / float(n_pop - 1)
        div_contribution_rank = div_rank[i] / float(n_pop - 1)
        if (n_pop <= elite):
            population[i]['fitness'] = fit_rank
        else:
            population[i]['fitness'] = fit_rank + (1.0 - elite / float(n_pop)) * div_contribution_rank

############################################################################

# Function: Remove Duplicate Tours
def _unique_population(population):
    unique = {}
    for ind in population:
        key = tuple(ind['route'])
        if (key not in unique or ind['cost'] < unique[key]['cost']):
            unique[key] = ind
    return list(unique.values())

############################################################################

# Function: Survivor Selection
def _survivor_selection(population, population_size, elite, closest):
    population = _unique_population(population)
    _update_biased_fitness(population, elite, closest)
    while (len(population) > population_size):
        worst_idx = max(range(0, len(population)), key = lambda i: population[i]['fitness'])
        del population[worst_idx]
        _update_biased_fitness(population, elite, closest)
    population.sort(key = lambda ind: ind['cost'])
    return population

############################################################################

# Function: Binary Tournament
def _binary_tournament(population, rng):
    a, b = rng.sample(range(0, len(population)), 2)
    if (population[a]['fitness'] <= population[b]['fitness']):
        return population[a]
    return population[b]

############################################################################

# Function: Stop Condition
def _time_exceeded(start_time, time_limit):
    if (time_limit is None):
        return False
    return (time.time() - start_time) >= float(time_limit)

############################################################################

# Function: HGS for TSP
def hybrid_genetic_search(distance_matrix, population_size = 25, offspring_size = 40,
                          elite = 4, closest = 5, mutation_rate = 0.25,
                          candidates = 20, local_search = True,
                          local_search_passes = 50, iterations = 500,
                          max_no_improvement = 150, time_limit = None,
                          seed = None, verbose = True):
    """
    Hybrid Genetic Search for the Traveling Salesman Problem.

    Parameters
    ----------
    distance_matrix : numpy.ndarray
        Square distance/cost matrix.
    population_size : int
        Number of individuals preserved after survivor selection.
    offspring_size : int
        Number of children generated per iteration.
    elite : int
        Number of elite individuals protected in biased-fitness ranking.
    closest : int
        Number of closest individuals used to estimate diversity contribution.
    mutation_rate : float
        Probability of applying double-bridge mutation to a child.
    candidates : int
        Number of nearest neighbors used by granular 2-opt local search.
    local_search : bool
        If True, applies 2-opt local improvement to initial individuals and children.
    local_search_passes : int
        Maximum number of 2-opt improvement passes per local search call.
    iterations : int
        Maximum number of HGS generations.
    max_no_improvement : int
        Stop after this many generations without improving the incumbent.
    time_limit : float or None
        Optional wall-clock time limit in seconds.
    seed : int or None
        Random seed.
    verbose : bool
        If True, prints progress.

    Returns
    -------
    route : list
        Closed tour using pyCombinatorial's 1-indexed convention.
    distance : float
        Total tour distance.
    """
    distance_matrix    = _prepare_distance_matrix(distance_matrix)
    n                  = distance_matrix.shape[0]
    rng                = random.Random(seed)
    symmetric          = _is_symmetric(distance_matrix)
    candidate          = _candidate_lists(distance_matrix, candidates)
    population_size    = max(4, int(population_size))
    offspring_size     = max(1, int(offspring_size))
    elite              = max(1, int(elite))
    closest            = max(1, int(closest))
    iterations         = max(1, int(iterations))
    max_no_improvement = max(1, int(max_no_improvement))
    mutation_rate      = min(1.0, max(0.0, float(mutation_rate)))
    start_time         = time.time()

    # Initial population: randomized nearest-neighbor plus random tours.
    population = []
    initialization_size = max(population_size * 2, population_size + offspring_size)
    for i in range(0, initialization_size):
        if (_time_exceeded(start_time, time_limit) == True):
            break
        if (i < initialization_size // 2):
            route = _randomized_nearest_neighbor(distance_matrix, rng, restricted_candidate_list = 3)
        else:
            route = _random_route(n, rng)
        if (local_search == True):
            route, _ = _two_opt_local_search(distance_matrix, route, candidate, local_search_passes)
        population.append(_make_individual(distance_matrix, route, symmetric))

    population = _survivor_selection(population, population_size, elite, closest)
    best       = dict(population[0])
    no_improv  = 0

    for it in range(1, iterations + 1):
        if (_time_exceeded(start_time, time_limit) == True):
            break
        _update_biased_fitness(population, elite, closest)
        offspring = []
        for _ in range(0, offspring_size):
            if (_time_exceeded(start_time, time_limit) == True):
                break
            parent_a = _binary_tournament(population, rng)
            parent_b = _binary_tournament(population, rng)
            trials   = 0
            while (parent_a is parent_b and trials < 10):
                parent_b = _binary_tournament(population, rng)
                trials   = trials + 1

            child_route = _ordered_crossover(parent_a['route'], parent_b['route'], rng)

            if (rng.random() <= mutation_rate):
                child_route = _double_bridge(child_route, rng)

            if (local_search == True):
                child_route, _ = _two_opt_local_search(distance_matrix, child_route, candidate, local_search_passes)

            offspring.append(_make_individual(distance_matrix, child_route, symmetric))

        population = _survivor_selection(population + offspring, population_size, elite, closest)

        if (population[0]['cost'] < best['cost'] - 1e-12):
            best      = dict(population[0])
            no_improv = 0
        else:
            no_improv = no_improv + 1

        if (verbose == True):
            print('Generation = ', it, 'Distance = ', round(best['cost'], 4))

        if (no_improv >= max_no_improvement):
            break

    route, distance = _to_city_tour(distance_matrix, best['route'])
    return route, distance

############################################################################
