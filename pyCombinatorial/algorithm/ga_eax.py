############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: Genetic Algorithm with Edge Assembly Crossover (GA-EAX)

# GitHub Repository: <https://github.com/Valdecy>

############################################################################

# Required Libraries
import numpy as np
import math
import random

from collections import Counter

############################################################################

# Function: Tour Distance
def distance_calc(distance_matrix, city_tour):
    route = city_tour[0] if isinstance(city_tour, (list, tuple)) and len(city_tour) > 0 and isinstance(city_tour[0], (list, tuple, np.ndarray)) else city_tour
    distance = 0.0
    for k in range(0, len(route) - 1):
        m = k + 1
        distance = distance + distance_matrix[route[k] - 1, route[m] - 1]
    return float(distance)

# Function: 2_opt
def local_search_2_opt(distance_matrix, city_tour, recursive_seeding = -1, verbose=True):
    route = list(city_tour[0])
    if len(route) > 1 and route[0] == route[-1]:
        route = route[:-1]
    n = len(route)
    if n <= 3:
        closed = route + [route[0]]
        return closed, float(distance_calc(distance_matrix, [closed, 0]))

    best_distance = float(city_tour[1]) if city_tour[1] not in (None, 0) else float(distance_calc(distance_matrix, [route + [route[0]], 0]))
    iteration     = 0

    while True:
        improved = False
        if verbose:
            print('Iteration = ', iteration, 'Distance = ', round(best_distance, 2))

        for i in range(0, n - 1):
            a = route[i - 1]
            b = route[i]
            for j in range(i + 1, n):
                c = route[j]
                d = route[(j + 1) % n]
                if a == c or b == d:
                    continue
                delta = distance_matrix[a - 1, c - 1] + distance_matrix[b - 1, d - 1] - distance_matrix[a - 1, b - 1] - distance_matrix[c - 1, d - 1]
                if delta < -1e-12:
                    route[i:j + 1] = reversed(route[i:j + 1])
                    best_distance = float(best_distance + delta)
                    improved = True
                    break
            if improved:
                break

        iteration = iteration + 1
        if recursive_seeding >= 0:
            if iteration > recursive_seeding:
                break
            if not improved:
                break
        else:
            if not improved:
                break

    closed = route + [route[0]]
    return closed, float(best_distance)

############################################################################

# Internal Utilities
def _route_0_to_1(route_0):
    return [node + 1 for node in route_0] + [route_0[0] + 1]


def _route_1_to_0(route_1):
    route = list(route_1)
    if len(route) > 1 and route[0] == route[-1]:
        route = route[:-1]
    return [node - 1 for node in route]

def _route_distance_0(distance_matrix, route_0):
    distance = 0.0
    n = len(route_0)
    for i in range(n):
        distance = distance + distance_matrix[route_0[i], route_0[(i + 1) % n]]
    return float(distance)

def _normalize_edge(i, j):
    return (i, j) if i <= j else (j, i)

def _edge_set_from_route(route_0):
    return {_normalize_edge(route_0[i], route_0[(i + 1) % len(route_0)]) for i in range(len(route_0))}

def _adjacency_from_route(route_0):
    n = len(route_0)
    adj = [set() for _ in range(n)]
    for i in range(n):
        a = route_0[i]
        b = route_0[(i + 1) % n]
        adj[a].add(b)
        adj[b].add(a)
    return adj

def _route_from_adjacency(adj, start=0):
    route = [start]
    prev  = -1
    curr  = start
    while True:
        nbrs = list(adj[curr])
        if len(nbrs) != 2:
            raise ValueError('Adjacency structure is not a Hamiltonian cycle')
        nxt = nbrs[0] if nbrs[0] != prev else nbrs[1]
        if nxt == start:
            break
        route.append(nxt)
        prev, curr = curr, nxt
        if len(route) > len(adj):
            raise ValueError('Cycle reconstruction overflow')
    if len(route) != len(adj):
        raise ValueError('Reconstructed route does not include all nodes')
    return route

def _valid_degrees(adj):
    return all(len(nbrs) == 2 for nbrs in adj)

def _connected_components(adj):
    visited    = [False] * len(adj)
    components = []
    for s in range(len(adj)):
        if visited[s]:
            continue
        stack      = [s]
        visited[s] = True
        comp       = []
        while stack:
            u = stack.pop()
            comp.append(u)
            for v in adj[u]:
                if not visited[v]:
                    visited[v] = True
                    stack.append(v)
        components.append(comp)
    return components

def _cycle_route_from_component(adj, component):
    start = component[0]
    route = [start]
    prev  = -1
    curr  = start
    while True:
        nbrs = list(adj[curr])
        nxt  = nbrs[1] if nbrs[0] == prev else nbrs[0]
        if nxt == start:
            break
        route.append(nxt)
        prev, curr = curr, nxt
    return route

def _cycle_edges_from_component(adj, component):
    route = _cycle_route_from_component(adj, component)
    return [_normalize_edge(route[i], route[(i + 1) % len(route)]) for i in range(len(route))]

def _nearest_city_list(distance_matrix):
    n    = distance_matrix.shape[0]
    near = []
    for i in range(n):
        order = np.argsort(distance_matrix[i, :]).tolist()
        near.append(order)
    return near

def _random_route(n, rng, initial_location=-1):
    route = list(range(n))
    if initial_location != -1:
        start = max(0, min(n - 1, int(initial_location) - 1))
        rest  = [i for i in route if i != start]
        rng.shuffle(rest)
        return [start] + rest
    rng.shuffle(route)
    return route

def _prepare_initial_route(distance_matrix, route, local_search = True):
    route_0  = _route_1_to_0(route) if min(route) >= 1 else list(route)
    closed_1 = _route_0_to_1(route_0)
    value    = distance_calc(distance_matrix, [closed_1, 0])
    if local_search:
        closed_1, value = local_search_2_opt(distance_matrix, [closed_1, value], recursive_seeding=-1, verbose=False)
        route_0         = _route_1_to_0(closed_1)
    return route_0, float(value)

def _make_population(distance_matrix, population_size, rng, local_search = True, initial_location = -1, initial_population = None):
    population = []
    n          = distance_matrix.shape[0]
    if initial_population is not None and len(initial_population) > 0:
        for route in initial_population:
            route_0, value = _prepare_initial_route(distance_matrix, route, local_search=local_search)
            population.append({'route': route_0, 'distance': value})
            if len(population) >= population_size:
                break
    while len(population) < population_size:
        route_0  = _random_route(n, rng, initial_location=initial_location)
        closed_1 = _route_0_to_1(route_0)
        value    = distance_calc(distance_matrix, [closed_1, 0])
        if local_search:
            closed_1, value = local_search_2_opt(distance_matrix, [closed_1, value], recursive_seeding=-1, verbose=False)
            route_0         = _route_1_to_0(closed_1)
        population.append({'route': route_0, 'distance': float(value)})
    return population

def _compute_edge_frequency(population):
    edge_freq = Counter()
    for individual in population:
        for edge in _edge_set_from_route(individual['route']):
            edge_freq[edge] += 1
    return edge_freq

def _fallback_recombine(parent_a, parent_b, distance_matrix, near_cities, rng):
    n       = len(parent_a)
    adj_a   = _adjacency_from_route(parent_a)
    adj_b   = _adjacency_from_route(parent_b)
    start   = rng.randrange(n)
    route   = [start]
    visited = {start}
    curr    = start
    while len(route) < n:
        candidates = list((adj_a[curr] | adj_b[curr]) - visited)
        if len(candidates) > 0:
            nxt = min(candidates, key=lambda node: distance_matrix[curr, node])
        else:
            remaining = [node for node in near_cities[curr] if node not in visited]
            if len(remaining) == 0:
                remaining = [node for node in range(n) if node not in visited]
            nxt = remaining[0]
        route.append(nxt)
        visited.add(nxt)
        curr = nxt
    return route

def _extract_ab_cycles(parent_a, parent_b, distance_matrix, rng):
    n       = len(parent_a)
    edges_a = _edge_set_from_route(parent_a)
    edges_b = _edge_set_from_route(parent_b)
    only_a  = set(edges_a - edges_b)
    only_b  = set(edges_b - edges_a)
    adj_a   = [[] for _ in range(n)]
    adj_b   = [[] for _ in range(n)]
    for u, v in only_a:
        adj_a[u].append(v)
        adj_a[v].append(u)
    for u, v in only_b:
        adj_b[u].append(v)
        adj_b[v].append(u)
    cycles    = []
    max_steps = 4 * n + 10
    while len(only_a) > 0:
        start_edge = rng.choice(tuple(only_a))
        u, v       = start_edge
        a_edges    = [(u, v)]
        b_edges    = []
        node_set   = {u, v}
        prev       = u
        curr       = v
        next_type  = 'B'
        ok         = False
        steps      = 0
        while steps < max_steps:
            steps = steps + 1
            candidates = list(adj_b[curr]) if next_type == 'B' else list(adj_a[curr])
            if len(candidates) > 1 and prev in candidates:
                candidates = [x for x in candidates if x != prev]
            if len(candidates) == 0:
                break
            preferred = []
            for nxt in candidates:
                edge = _normalize_edge(curr, nxt)
                if next_type == 'B' or edge in only_a:
                    preferred.append(nxt)
            if len(preferred) > 0:
                candidates = preferred
            nxt  = rng.choice(candidates)
            edge = (curr, nxt)
            if next_type == 'B':
                b_edges.append(edge)
                next_type = 'A'
            else:
                a_edges.append(edge)
                next_type = 'B'
            node_set.add(nxt)
            prev, curr = curr, nxt
            if curr == u and next_type == 'A':
                ok = True
                break
        if ok and len(a_edges) == len(b_edges) and len(a_edges) > 0:
            for edge in a_edges:
                only_a.discard(_normalize_edge(edge[0], edge[1]))
            gain = sum(distance_matrix[i, j] for i, j in a_edges) - sum(distance_matrix[i, j] for i, j in b_edges)
            cycles.append({'a_edges': a_edges, 'b_edges': b_edges, 'gain': float(gain), 'node_set': set(node_set)})
        else:
            only_a.discard(start_edge)
    return cycles

def _apply_cycle(adj, cycle):
    for u, v in cycle['a_edges']:
        adj[u].discard(v)
        adj[v].discard(u)
    for u, v in cycle['b_edges']:
        adj[u].add(v)
        adj[v].add(u)

def _reconnect_subtours(adj, distance_matrix, near_cities):
    while True:
        components = _connected_components(adj)
        if len(components) <= 1:
            return adj
        comp_index = {}
        for idx, comp in enumerate(components):
            for node in comp:
                comp_index[node] = idx
        center       = min(components, key=len)
        center_nodes = set(center)
        center_edges = _cycle_edges_from_component(adj, center)
        best_move    = None
        best_gain    = -float('inf')
        for a, b in center_edges:
            for anchor in (a, b):
                for c in near_cities[anchor][1:]:
                    if c in center_nodes:
                        continue
                    for d in list(adj[c]):
                        if comp_index[d] != comp_index[c]:
                            continue
                        delta_1 = distance_matrix[a, b] + distance_matrix[c, d] - distance_matrix[a, c] - distance_matrix[b, d]
                        if delta_1 > best_gain:
                            best_gain = delta_1
                            best_move = (a, b, c, d, 0)
                        delta_2 = distance_matrix[a, b] + distance_matrix[c, d] - distance_matrix[a, d] - distance_matrix[b, c]
                        if delta_2 > best_gain:
                            best_gain = delta_2
                            best_move = (a, b, c, d, 1)
        if best_move is None:
            other_components = [comp for comp in components if comp is not center]
            for a, b in center_edges:
                for comp in other_components:
                    for c, d in _cycle_edges_from_component(adj, comp):
                        delta_1 = distance_matrix[a, b] + distance_matrix[c, d] - distance_matrix[a, c] - distance_matrix[b, d]
                        if delta_1 > best_gain:
                            best_gain = delta_1
                            best_move = (a, b, c, d, 0)
                        delta_2 = distance_matrix[a, b] + distance_matrix[c, d] - distance_matrix[a, d] - distance_matrix[b, c]
                        if delta_2 > best_gain:
                            best_gain = delta_2
                            best_move = (a, b, c, d, 1)
        if best_move is None:
            raise RuntimeError('Failed to reconnect subtours generated by EAX')
        a, b, c, d, mode = best_move
        adj[a].discard(b)
        adj[b].discard(a)
        adj[c].discard(d)
        adj[d].discard(c)
        if mode == 0:
            adj[a].add(c)
            adj[c].add(a)
            adj[b].add(d)
            adj[d].add(b)
        else:
            adj[a].add(d)
            adj[d].add(a)
            adj[b].add(c)
            adj[c].add(b)

def _build_multi_cycle_set(cycles, center_idx, max_cycles = 3):
    selected  = [center_idx]
    used       = set(cycles[center_idx]['node_set'])
    candidates = [idx for idx in range(len(cycles)) if idx != center_idx]
    candidates = sorted(candidates, key = lambda idx: cycles[idx]['gain'], reverse = True)
    for idx in candidates:
        if len(selected) >= max_cycles:
            break
        overlap = len(used & cycles[idx]['node_set'])
        if overlap <= max(1, len(cycles[idx]['node_set']) // 4):
            selected.append(idx)
            used |= cycles[idx]['node_set']
    return selected

def _adp_loss(old_edges, new_edges, edge_freq):
    removed = old_edges - new_edges
    added = new_edges - old_edges
    penalty = 0.0
    for edge in removed:
        penalty = penalty - max(edge_freq.get(edge, 0) - 1, 0)
    for edge in added:
        penalty = penalty + edge_freq.get(edge, 0)
    return max(float(penalty), 1e-8)

def _entropy_loss(old_edges, new_edges, edge_freq, population_size):
    def entropy_term(count):
        if count <= 0 or population_size <= 0:
            return 0.0
        p = count / float(population_size)
        return -p * math.log(p)
    changed = (old_edges - new_edges) | (new_edges - old_edges)
    delta   = 0.0
    for edge in changed:
        before = edge_freq.get(edge, 0)
        after = before
        if edge in old_edges and edge not in new_edges:
            after = after - 1
        if edge in new_edges and edge not in old_edges:
            after = after + 1
        delta = delta + (entropy_term(after) - entropy_term(before))
    return max(float(-delta), 1e-8)

def _eax_candidate_from_pair(parent_a, parent_b, distance_matrix, near_cities, edge_freq, population_size, offspring_size, stage_mode, diversity_mode, rng):
    cycles = _extract_ab_cycles(parent_a, parent_b, distance_matrix, rng)
    if len(cycles) == 0:
        child = _fallback_recombine(parent_a, parent_b, distance_matrix, near_cities, rng)
        return child, _route_distance_0(distance_matrix, child)
    order = list(range(len(cycles)))
    if stage_mode == 'single':
        rng.shuffle(order)
    else:
        order = sorted(order, key=lambda idx: cycles[idx]['gain'], reverse=True)
    old_edges     = _edge_set_from_route(parent_a)
    best_child    = None
    best_distance = float('inf')
    best_point    = -float('inf')
    for idx in order[:min(offspring_size, len(order))]:
        selected_cycles = [idx] if stage_mode == 'single' else _build_multi_cycle_set(cycles, idx)
        adj             = _adjacency_from_route(parent_a)
        valid           = True
        for cycle_idx in selected_cycles:
            _apply_cycle(adj, cycles[cycle_idx])
            if not _valid_degrees(adj):
                valid = False
                break
        if valid:
            try:
                _reconnect_subtours(adj, distance_matrix, near_cities)
                if not _valid_degrees(adj):
                    valid = False
                else:
                    child = _route_from_adjacency(adj, start=parent_a[0])
            except Exception:
                valid = False
        if not valid:
            child      = _fallback_recombine(parent_a, parent_b, distance_matrix, near_cities, rng)
        child_distance = _route_distance_0(distance_matrix, child)
        gain           = _route_distance_0(distance_matrix, parent_a) - child_distance
        if gain <= 0:
            continue
        if child == parent_b:
            continue
        new_edges = _edge_set_from_route(child)
        if diversity_mode == 'greedy':
            loss = 1.0
        elif diversity_mode == 'distance':
            loss = _adp_loss(old_edges, new_edges, edge_freq)
        else:
            loss = _entropy_loss(old_edges, new_edges, edge_freq, population_size)
        point = gain / max(loss, 1e-8)
        if point > best_point:
            best_point    = point
            best_child    = child
            best_distance = child_distance
    if best_child is None:
        child = _fallback_recombine(parent_a, parent_b, distance_matrix, near_cities, rng)
        return child, _route_distance_0(distance_matrix, child)
    return best_child, float(best_distance)

############################################################################

# Function: Genetic Algorithm with Edge Assembly Crossover
def genetic_algorithm_edge_assembly_crossover(distance_matrix, population_size = 30, offspring_size = 30, generations = 500, local_search = True, verbose = True, stage_switch = True, diversity_mode = 'entropy'):
    distance_matrix = np.array(distance_matrix, dtype = float)
    if distance_matrix.ndim != 2 or distance_matrix.shape[0] != distance_matrix.shape[1]:
        raise ValueError('distance_matrix must be a square matrix')
    rng         = random.Random(None)
    near_cities = _nearest_city_list(distance_matrix)
    population  = _make_population(distance_matrix   = distance_matrix,
                                  population_size    = population_size,
                                  rng                = rng,
                                  local_search       = True,
                                  initial_location   = -1,
                                  initial_population = None)

    edge_freq                  = _compute_edge_frequency(population)
    best_individual            = min(population, key=lambda item: item['distance'])
    best_route                 = list(best_individual['route'])
    best_distance              = float(best_individual['distance'])
    #history                    = [{'generation': 0, 'best': best_distance, 'average': float(np.mean([item['distance'] for item in population])), 'stage': 1}]
    stage                      = 1
    stage_mode                 = 'single'
    no_improve                 = 0
    stage_reference_generation = 0
    max_stag_best              = 0
    for generation in range(1, generations + 1):
        mating_order  = list(range(population_size))
        rng.shuffle(mating_order)
        mating_order  = mating_order + [mating_order[0]]
        previous_best = best_distance
        for s in range(population_size):
            parent_index = mating_order[s]
            mate_index   = mating_order[s + 1]
            parent_a     = list(population[parent_index]['route'])
            parent_b     = list(population[mate_index]['route'])
            child_route, child_distance = _eax_candidate_from_pair(parent_a        = parent_a,
                                                                   parent_b        = parent_b,
                                                                   distance_matrix = distance_matrix,
                                                                   near_cities     = near_cities,
                                                                   edge_freq       = edge_freq,
                                                                   population_size = population_size,
                                                                   offspring_size  = offspring_size,
                                                                   stage_mode      = stage_mode,
                                                                   diversity_mode  = diversity_mode,
                                                                   rng             = rng)

            if local_search:
                child_closed                 = _route_0_to_1(child_route)
                child_closed, child_distance = local_search_2_opt(distance_matrix, [child_closed, child_distance],
                                                                  recursive_seeding = -1,
                                                                  verbose           = False)
                child_route                  = _route_1_to_0(child_closed)

            if child_distance < population[parent_index]['distance']:
                old_edges = _edge_set_from_route(population[parent_index]['route'])
                new_edges = _edge_set_from_route(child_route)
                for edge in old_edges - new_edges:
                    edge_freq[edge] = max(0, edge_freq.get(edge, 0) - 1)
                    if edge_freq[edge] == 0:
                        del edge_freq[edge]
                for edge in new_edges - old_edges:
                    edge_freq[edge] = edge_freq.get(edge, 0) + 1
                population[parent_index] = {'route': child_route, 'distance': float(child_distance)}

        current_best_individual = min(population, key=lambda item: item['distance'])
        current_best_distance   = float(current_best_individual['distance'])
        current_best_route      = list(current_best_individual['route'])
        current_average         = float(np.mean([item['distance'] for item in population]))

        if current_best_distance < best_distance:
            best_distance = current_best_distance
            best_route    = current_best_route
            no_improve    = 0
        else:
            no_improve    = no_improve + 1

        if stage_switch:
            threshold = max(1, int(1500 / max(1, offspring_size)))
            if stage == 1:
                if no_improve == threshold and max_stag_best == 0:
                    max_stag_best = max(1, int(generation / 10))
                elif max_stag_best != 0 and no_improve >= max_stag_best:
                    stage                      = 2
                    stage_mode                 = 'multi'
                    no_improve                 = 0
                    max_stag_best              = 0
                    stage_reference_generation = generation
            else:
                if no_improve == threshold and max_stag_best == 0:
                    max_stag_best = max(1, int(max(1, generation - stage_reference_generation) / 10))
                elif max_stag_best != 0 and no_improve >= max_stag_best:
                    #history.append({'generation': generation, 'best': best_distance, 'average': current_average, 'stage': stage})
                    break

        #history.append({'generation': generation, 'best': best_distance, 'average': current_average, 'stage': stage})

        if verbose:
            print('Generation = ', generation,
                  'Stage = ',      stage,
                  'Best = ',       round(best_distance, 2),
                  'Average = ',    round(current_average, 2),
                  'No Improve = ', no_improve)

        if abs(current_average - current_best_distance) < 1e-10:
            break
        if current_best_distance >= previous_best and generation >= generations:
            break

    best_route_closed = _route_0_to_1(best_route)
    return best_route_closed, best_distance

############################################################################