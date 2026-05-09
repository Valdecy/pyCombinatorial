############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email: valdecy.pereira@gmail.com
# Lesson: Lin-Kernighan-Helsgaun - Inspired Heuristic

############################################################################

# Required Libraries
import copy
import heapq
import random
import numpy as np

try:
    from numba import njit
    _NUMBA_AVAILABLE = True
except Exception:
    _NUMBA_AVAILABLE = False
    def njit(*args, **kwargs):
        def wrapper(func):
            return func
        return wrapper

############################################################################

def distance_calc(distance_matrix, city_tour):
    route    = city_tour[0] if isinstance(city_tour, (list, tuple)) and len(city_tour) > 0 and isinstance(city_tour[0], (list, tuple, np.ndarray)) else city_tour
    distance = 0.0
    for k in range(0, len(route) - 1):
        distance = distance + distance_matrix[route[k] - 1, route[k + 1] - 1]
    return float(distance)

def _normalize_route(route):
    route = list(route)
    if len(route) > 1 and route[0] == route[-1]:
        route = route[:-1]
    return route

def _close_route(route):
    route = list(route)
    if len(route) > 0 and route[0] != route[-1]:
        route = route + [route[0]]
    return route

def _validate_route(route, n):
    route = _normalize_route(route)
    return len(route) == n and len(set(route)) == n

def _route_to_zero(route):
    route = _normalize_route(route)
    return np.array([int(x) - 1 for x in route], dtype = np.int64)

def _route_to_one(route0):
    return [int(x) + 1 for x in route0.tolist()]

def _tour_distance_zero(distance_matrix, route0):
    n = route0.shape[0]
    total = 0.0
    for i in range(0, n):
        total = total + distance_matrix[route0[i], route0[(i + 1) % n]]
    return float(total)

############################################################################

@njit(cache = False)
def _successor_predecessor_from_route_numba(route0):
    n = route0.shape[0]
    succ = np.empty(n, dtype = np.int64)
    pred = np.empty(n, dtype = np.int64)

    for i in range(n):
        a = route0[i]
        b = route0[(i + 1) % n]
        succ[a] = b
        pred[b] = a

    return succ, pred

def _successor_predecessor_from_route(route0):
    if _NUMBA_AVAILABLE:
        return _successor_predecessor_from_route_numba(route0)
    n = route0.shape[0]
    succ = np.empty(n, dtype = np.int64)
    pred = np.empty(n, dtype = np.int64)
    for i in range(n):
        a = route0[i]
        b = route0[(i + 1) % n]
        succ[a] = b
        pred[b] = a
    return succ, pred

@njit(cache = False)
def _route_from_successor_numba(succ, start):
    n = succ.shape[0]
    route = np.empty(n, dtype = np.int64)
    node = start

    for i in range(n):
        route[i] = node
        node = succ[node]

    return route

def _route_from_successor(succ, start = 0):
    if _NUMBA_AVAILABLE:
        return _route_from_successor_numba(succ, start)
    n = succ.shape[0]
    route = np.empty(n, dtype = np.int64)
    node = start
    for i in range(n):
        route[i] = node
        node = succ[node]
    return route

############################################################################

def _route_and_pos_from_successor(succ, start = 0):
    route = _route_from_successor(succ, start = start)
    pos = np.empty(route.shape[0], dtype = np.int64)
    for i in range(route.shape[0]):
        pos[int(route[i])] = i
    return route, pos

def _path_length_successor(succ, start, end):
    start = int(start)
    end = int(end)
    length = 1
    node = start
    while node != end:
        node = int(succ[node])
        length = length + 1
    return length

def _reverse_path_in_successor(succ, pred, start, end):
    start = int(start)
    end = int(end)
    node = start

    while True:
        nxt = int(succ[node])
        prv = int(pred[node])
        succ[node] = prv
        pred[node] = nxt
        if node == end:
            break
        node = nxt

class _LinkedTour:
    __slots__ = ('n', 'succ', 'pred', 'start')

    def __init__(self, route0):
        route0 = np.ascontiguousarray(route0.astype(np.int64))
        self.n = int(route0.shape[0])
        self.succ, self.pred = _successor_predecessor_from_route(route0)
        self.start = int(route0[0]) if self.n > 0 else 0

    def clone(self):
        other = object.__new__(_LinkedTour)
        other.n = self.n
        other.succ = self.succ.copy()
        other.pred = self.pred.copy()
        other.start = self.start
        return other

    def to_route(self, start = None):
        if start is None:
            start = self.start
        return _route_from_successor(self.succ, start = int(start))

    def route_and_pos(self, start = None):
        if start is None:
            start = self.start
        return _route_and_pos_from_successor(self.succ, start = int(start))

    def neighbors(self, node):
        node = int(node)
        return int(self.succ[node]), int(self.pred[node])

    def apply_two_opt_nodes(self, a, b, c, d):
        a = int(a)
        b = int(b)
        c = int(c)
        d = int(d)

        if int(self.succ[a]) != b or int(self.succ[c]) != d:
            raise ValueError('2-opt move expects directed tour edges (a,b) and (c,d)')

        seg_len = _path_length_successor(self.succ, b, c)
        comp_len = self.n - seg_len

        if seg_len <= comp_len:
            _reverse_path_in_successor(self.succ, self.pred, b, c)
            self.succ[a] = c
            self.pred[c] = a
            self.succ[b] = d
            self.pred[d] = b
        else:
            _reverse_path_in_successor(self.succ, self.pred, d, a)
            self.succ[c] = a
            self.pred[a] = c
            self.succ[d] = b
            self.pred[b] = d

        self.start = a

@njit(cache = False)
def _reverse_segment_in_route_numba(route0, i, j):
    n = route0.shape[0]
    new_route = route0.copy()
    left = i + 1
    right = j

    while left < right:
        tmp = new_route[left]
        new_route[left] = new_route[right]
        new_route[right] = tmp
        left = left + 1
        right = right - 1

    return new_route

def _reverse_segment_in_route(route0, i, j):
    if _NUMBA_AVAILABLE:
        return _reverse_segment_in_route_numba(route0, i, j)
    new_route = route0.copy()
    new_route[i + 1:j + 1] = new_route[i + 1:j + 1][::-1]
    return new_route

############################################################################

def _mst_prim(weight_matrix, nodes):
    if len(nodes) <= 1:
        return [], 0.0

    start = nodes[0]
    visited = set([start])
    heap = []
    edges = []
    cost = 0.0

    for j in nodes:
        if j != start:
            heapq.heappush(heap, (weight_matrix[start, j], start, j))

    while len(visited) < len(nodes) and len(heap) > 0:
        w, i, j = heapq.heappop(heap)
        if j in visited:
            continue

        visited.add(j)
        edges.append((i, j))
        cost = cost + w

        for k in nodes:
            if k not in visited:
                heapq.heappush(heap, (weight_matrix[j, k], j, k))

    return edges, float(cost)

def _minimum_one_tree(distance_matrix, pi = None, root = 0):
    n = distance_matrix.shape[0]

    if pi is None:
        pi = np.zeros(n)

    weighted = distance_matrix + pi.reshape((n, 1)) + pi.reshape((1, n))

    nodes = [i for i in range(0, n) if i != root]
    mst_edges, mst_cost = _mst_prim(weighted, nodes)

    root_edges = sorted([(weighted[root, j], root, j) for j in nodes], key = lambda x: x[0])
    e1 = (root_edges[0][1], root_edges[0][2])
    e2 = (root_edges[1][1], root_edges[1][2])

    edges = mst_edges + [e1, e2]
    weighted_cost = mst_cost + root_edges[0][0] + root_edges[1][0]

    degree = np.zeros(n, dtype = int)
    for i, j in edges:
        degree[i] = degree[i] + 1
        degree[j] = degree[j] + 1

    lower_bound = weighted_cost - 2.0*np.sum(pi)
    return edges, degree, float(weighted_cost), float(lower_bound), weighted

def _subgradient_potentials(distance_matrix, root = 0, ascent_iterations = 100):
    n = distance_matrix.shape[0]
    pi = np.zeros(n, dtype = float)

    edges, degree, weighted_cost, lb, weighted = _minimum_one_tree(distance_matrix, pi = pi, root = root)

    best_pi = pi.copy()
    best_edges = edges
    best_degree = degree.copy()
    best_lb = lb

    positive_distances = distance_matrix[distance_matrix > 0]
    scale = float(np.mean(positive_distances)) if positive_distances.size > 0 else 1.0

    total_iterations = max(0, int(ascent_iterations))
    if total_iterations == 0:
        return best_pi, best_edges, best_degree, best_lb

    period = max(4, total_iterations // 4)
    step_scale = scale
    prev_g = np.zeros(n, dtype = float)

    t = 0
    while t < total_iterations:
        for _ in range(period):
            if t >= total_iterations:
                break

            edges, degree, weighted_cost, lb, weighted = _minimum_one_tree(distance_matrix, pi = pi, root = root)

            if lb > best_lb + 1e-12:
                best_lb = lb
                best_pi = pi.copy()
                best_edges = edges
                best_degree = degree.copy()

            g = (degree - 2).astype(float)
            norm = float(np.dot(g, g))

            if norm <= 1e-12:
                best_pi = pi.copy()
                best_edges = edges
                best_degree = degree.copy()
                best_lb = lb
                return best_pi, best_edges, best_degree, best_lb

            beta = 0.3 if t > 0 else 0.0
            direction = g + beta*(g - prev_g)
            dir_norm = float(np.dot(direction, direction))
            if dir_norm <= 1e-12:
                direction = g
                dir_norm = norm

            step = step_scale / np.sqrt(dir_norm)
            pi = pi + step*direction
            pi = pi - np.mean(pi)

            prev_g = g
            t = t + 1

        step_scale = 0.5*step_scale
        period = max(2, period // 2)

    return best_pi, best_edges, best_degree, best_lb

def _build_adjacency(n, edges, weights):
    adj = [[] for _ in range(0, n)]

    for i, j in edges:
        w = float(weights[i, j])
        adj[i].append((j, w))
        adj[j].append((i, w))

    return adj

def _max_edge_on_path(adj, source, target):
    stack = [(source, -1, -np.inf)]
    visited = set()

    while len(stack) > 0:
        node, parent, current_max = stack.pop()

        if node == target:
            return current_max

        visited.add(node)

        for nxt, w in adj[node]:
            if nxt == parent or nxt in visited:
                continue
            stack.append((nxt, node, max(current_max, w)))

    return np.inf

def _root_replacement_alpha(root, j, root_edges_sorted, weighted):
    selected_nodes = [edge[2] for edge in root_edges_sorted[:2]]

    if j in selected_nodes:
        return 0.0

    largest_selected_weight = max(root_edges_sorted[0][0], root_edges_sorted[1][0])
    return float(weighted[root, j] - largest_selected_weight)

def _exact_alpha_values(distance_matrix, pi, one_tree_edges, root = 0):
    n = distance_matrix.shape[0]
    weighted = distance_matrix + pi.reshape((n, 1)) + pi.reshape((1, n))

    tree_set = set((min(i, j), max(i, j)) for i, j in one_tree_edges)

    mst_edges = [(i, j) for i, j in one_tree_edges if i != root and j != root]
    mst_adj = _build_adjacency(n, mst_edges, weighted)

    root_edges_sorted = sorted(
        [(weighted[root, j], root, j) for j in range(0, n) if j != root],
        key = lambda x: x[0]
    )

    alpha = np.zeros((n, n), dtype = float)

    for i in range(0, n):
        for j in range(i + 1, n):
            a, b = min(i, j), max(i, j)

            if (a, b) in tree_set:
                val = 0.0

            elif i == root or j == root:
                other = j if i == root else i
                val = _root_replacement_alpha(root, other, root_edges_sorted, weighted)

            else:
                max_w = _max_edge_on_path(mst_adj, i, j)
                val = float(weighted[i, j] - max_w)

            if val < 0:
                val = 0.0

            alpha[i, j] = val
            alpha[j, i] = val

    return alpha

def _alpha_nearness_candidates(distance_matrix, candidate_size = 20, ascent_iterations = 100, root = 0, extra_nearest = True):
    n = distance_matrix.shape[0]
    candidate_size = max(1, min(candidate_size, n - 1))

    pi, one_tree_edges, degree, lb = _subgradient_potentials(
        distance_matrix,
        root = root,
        ascent_iterations = ascent_iterations
    )

    alpha = _exact_alpha_values(
        distance_matrix,
        pi,
        one_tree_edges,
        root = root
    )

    candidates = []
    for i in range(0, n):
        scored = []
        for j in range(0, n):
            if i == j:
                continue
            scored.append((alpha[i, j], distance_matrix[i, j], j))
        scored = sorted(scored, key = lambda x: (x[0], x[1]))
        candidates.append([j for _, _, j in scored[:candidate_size]])

    if extra_nearest:
        nearest = _nearest_candidates(distance_matrix, candidate_size = candidate_size)
        candidates = _merge_candidates(candidates, nearest, candidate_size, distance_matrix = distance_matrix)

    return candidates, alpha, pi, one_tree_edges, lb

def _nearest_candidates(distance_matrix, candidate_size = 20):
    n = distance_matrix.shape[0]
    candidate_size = max(1, min(candidate_size, n - 1))
    candidates = []

    for i in range(0, n):
        order = np.argsort(distance_matrix[i, :]).tolist()
        order = [j for j in order if j != i]
        candidates.append(order[:candidate_size])

    return candidates

def _clean_candidate_rows(candidates, candidate_size):
    cleaned = []
    for i in range(len(candidates)):
        seen = set()
        row = []
        for j in candidates[i]:
            j = int(j)
            if j != i and j not in seen:
                row.append(j)
                seen.add(j)
            if len(row) >= candidate_size:
                break
        cleaned.append(row)
    return cleaned

def _make_candidate_sets_symmetric(candidates, candidate_size, distance_matrix = None):
    n = len(candidates)
    sym = [list(row) for row in candidates]

    for i in range(n):
        for j in list(sym[i]):
            if j != i and i not in sym[j]:
                sym[j].append(i)

    cleaned = []
    for i in range(n):
        row = [int(j) for j in sym[i] if int(j) != i]
        row = list(dict.fromkeys(row))
        if distance_matrix is not None:
            row = sorted(row, key = lambda j: (float(distance_matrix[i, j]), j))
        cleaned.append(row[:candidate_size])

    return _clean_candidate_rows(cleaned, candidate_size)

def _merge_candidates(alpha_candidates, nearest_candidates, candidate_size, distance_matrix = None):
    n = len(alpha_candidates)
    merged = []

    for i in range(0, n):
        row = []
        seen = set()

        for j in alpha_candidates[i] + nearest_candidates[i]:
            j = int(j)
            if j != i and j not in seen:
                row.append(j)
                seen.add(j)

        if distance_matrix is not None:
            row = sorted(row, key = lambda j: (float(distance_matrix[i, j]), j))

        merged.append(row[:candidate_size])

    return _make_candidate_sets_symmetric(merged, candidate_size, distance_matrix = distance_matrix)

def _augment_candidates_with_route(candidates, route0, candidate_size, distance_matrix = None):
    n = route0.shape[0]
    augmented = [list(row) for row in candidates]

    for i in range(n):
        a = int(route0[i])
        b = int(route0[(i + 1) % n])
        c = int(route0[(i - 1) % n])

        if b not in augmented[a]:
            augmented[a].insert(0, b)
        if a not in augmented[b]:
            augmented[b].insert(0, a)

        if c not in augmented[a]:
            augmented[a].insert(0, c)
        if a not in augmented[c]:
            augmented[c].insert(0, a)

    augmented = _clean_candidate_rows(augmented, max(candidate_size, max(len(row) for row in augmented)))
    return _make_candidate_sets_symmetric(augmented, candidate_size, distance_matrix = distance_matrix)


def _candidate_array(candidates):
    max_len = max(len(row) for row in candidates)
    arr = -np.ones((len(candidates), max_len), dtype = np.int64)
    for i, row in enumerate(candidates):
        arr[i, :len(row)] = np.array(row, dtype = np.int64)
    return arr

############################################################################

def _nearest_neighbour_solution(distance_matrix, initial_location = -1, random_start = False, rng = None):
    n = distance_matrix.shape[0]

    if rng is None:
        rng = random.Random(None)

    if random_start == True:
        start = rng.randrange(n)
    else:
        start = 0 if initial_location == -1 else max(0, min(n - 1, int(initial_location) - 1))

    unvisited = set(range(0, n))
    route = [start]
    unvisited.remove(start)

    while len(unvisited) > 0:
        i = route[-1]
        j = min(unvisited, key = lambda node: distance_matrix[i, node])
        route.append(j)
        unvisited.remove(j)

    return np.array(route, dtype = np.int64), _tour_distance_zero(distance_matrix, np.array(route, dtype = np.int64))

def _randomized_greedy_solution(distance_matrix, candidate_size = 5, rng = None):
    n = distance_matrix.shape[0]

    if rng is None:
        rng = random.Random(None)

    start = rng.randrange(n)
    unvisited = set(range(0, n))
    route = [start]
    unvisited.remove(start)

    while len(unvisited) > 0:
        i = route[-1]
        ordered = sorted(list(unvisited), key = lambda node: distance_matrix[i, node])
        rcl = ordered[:max(1, min(candidate_size, len(ordered)))]
        j = rng.choice(rcl)
        route.append(j)
        unvisited.remove(j)

    route0 = np.array(route, dtype = np.int64)
    return route0, _tour_distance_zero(distance_matrix, route0)

def _alpha_greedy_solution(distance_matrix, candidates, alpha = None, initial_location = -1, rng = None):
    n = distance_matrix.shape[0]

    if rng is None:
        rng = random.Random(None)

    start = 0 if initial_location == -1 else max(0, min(n - 1, int(initial_location) - 1))
    unvisited = set(range(0, n))
    route = [start]
    unvisited.remove(start)

    while len(unvisited) > 0:
        i = route[-1]
        cand_unvisited = [j for j in candidates[i] if j in unvisited]

        if len(cand_unvisited) > 0:
            if alpha is None:
                j = min(cand_unvisited, key = lambda node: (distance_matrix[i, node], node))
            else:
                j = min(cand_unvisited, key = lambda node: (alpha[i, node], distance_matrix[i, node], node))
        else:
            j = min(unvisited, key = lambda node: (distance_matrix[i, node], node))

        route.append(int(j))
        unvisited.remove(int(j))

    route0 = np.array(route, dtype = np.int64)
    return route0, _tour_distance_zero(distance_matrix, route0)

############################################################################

@njit(cache = False)
def _positions_numba(route0):
    n = route0.shape[0]
    pos = np.empty(n, dtype = np.int64)
    for i in range(n):
        pos[route0[i]] = i
    return pos

@njit(cache = False)
def _two_opt_delta_numba(distance_matrix, route0, i, j):
    n = route0.shape[0]
    a = route0[i]
    b = route0[(i + 1) % n]
    c = route0[j]
    d = route0[(j + 1) % n]
    return distance_matrix[a, c] + distance_matrix[b, d] - distance_matrix[a, b] - distance_matrix[c, d]

@njit(cache = False)
def _best_2opt_move_numba(distance_matrix, route0, cand_arr):
    n = route0.shape[0]
    pos = _positions_numba(route0)

    best_delta = 0.0
    best_i = -1
    best_j = -1

    for i in range(n):
        b = route0[(i + 1) % n]

        for kk in range(cand_arr.shape[1]):
            c = cand_arr[b, kk]
            if c < 0:
                continue

            j = pos[c]

            if j == i or j == (i + 1) % n:
                continue
            if (j + 1) % n == i:
                continue

            ii = i
            jj = j
            if ii > jj:
                tmp = ii
                ii = jj
                jj = tmp

            if ii == 0 and jj == n - 1:
                continue

            delta = _two_opt_delta_numba(distance_matrix, route0, ii, jj)

            if delta < best_delta:
                best_delta = delta
                best_i = ii
                best_j = jj

    return best_delta, best_i, best_j

@njit(cache = False)
def _apply_2opt_numba(route0, i, j):
    return _reverse_segment_in_route_numba(route0, i, j)

@njit(cache = False)
def _tour_distance_numba(distance_matrix, route0):
    n = route0.shape[0]
    total = 0.0
    for i in range(n):
        total = total + distance_matrix[route0[i], route0[(i + 1) % n]]
    return total

############################################################################

def _best_2opt_move(distance_matrix, route0, cand_arr):
    if _NUMBA_AVAILABLE:
        return _best_2opt_move_numba(distance_matrix, route0, cand_arr)

    n = route0.shape[0]
    pos = {int(route0[i]): i for i in range(n)}

    best_delta = 0.0
    best_i = -1
    best_j = -1

    for i in range(n):
        b = int(route0[(i + 1) % n])

        for c in cand_arr[b]:
            if c < 0:
                continue

            j = pos[int(c)]

            if j == i or j == (i + 1) % n:
                continue
            if (j + 1) % n == i:
                continue

            ii, jj = i, j
            if ii > jj:
                ii, jj = jj, ii

            if ii == 0 and jj == n - 1:
                continue

            a0 = int(route0[ii])
            b0 = int(route0[(ii + 1) % n])
            c0 = int(route0[jj])
            d0 = int(route0[(jj + 1) % n])
            delta = distance_matrix[a0, c0] + distance_matrix[b0, d0] - distance_matrix[a0, b0] - distance_matrix[c0, d0]

            if delta < best_delta:
                best_delta = delta
                best_i = ii
                best_j = jj

    return best_delta, best_i, best_j

def _apply_2opt(route0, i, j):
    if _NUMBA_AVAILABLE:
        return _apply_2opt_numba(route0, i, j)
    return _reverse_segment_in_route(route0, i, j)

def _intensify_2opt(distance_matrix, route0, cand_arr, max_passes = 100, use_dont_look_bits = True):
    route0 = route0.copy()
    n = route0.shape[0]
    distance = _tour_distance_zero(distance_matrix, route0)
    tour = _LinkedTour(route0)
    dlb = np.zeros(n, dtype = np.uint8)

    for _ in range(max_passes):
        improved = False
        route_view, pos = tour.route_and_pos(start = int(route0[0]))

        for i in range(n):
            a = int(route_view[i])
            if use_dont_look_bits == True and dlb[a] == 1:
                continue

            found = False
            b = int(route_view[(i + 1) % n])

            for c in cand_arr[b]:
                if c < 0:
                    continue
                c = int(c)
                j = int(pos[c])

                if j == i or j == (i + 1) % n or (j + 1) % n == i:
                    continue

                ii, jj = (i, j) if i < j else (j, i)
                if ii == 0 and jj == n - 1:
                    continue

                a0 = int(route_view[ii])
                b0 = int(route_view[(ii + 1) % n])
                c0 = int(route_view[jj])
                d0 = int(route_view[(jj + 1) % n])
                delta = float(distance_matrix[a0, c0] + distance_matrix[b0, d0] - distance_matrix[a0, b0] - distance_matrix[c0, d0])

                if delta < 0.0:
                    tour.apply_two_opt_nodes(a0, b0, c0, d0)
                    distance = distance + delta

                    if use_dont_look_bits == True:
                        touched = {
                            a0,
                            b0,
                            c0,
                            d0,
                            int(tour.pred[a0]),
                            int(tour.succ[a0]),
                            int(tour.pred[b0]),
                            int(tour.succ[b0]),
                            int(tour.pred[c0]),
                            int(tour.succ[c0]),
                            int(tour.pred[d0]),
                            int(tour.succ[d0])
                        }
                        for node in touched:
                            dlb[node] = 0

                    improved = True
                    found = True
                    break

            if found == True:
                break

            if use_dont_look_bits == True:
                dlb[a] = 1

        if improved == False:
            break

    return tour.to_route(start = int(route0[0])), float(distance)

############################################################################

def _edge_cost(distance_matrix, a, b):
    return float(distance_matrix[int(a), int(b)])

def _build_pos(route0):
    return {int(route0[i]): i for i in range(route0.shape[0])}

def _apply_two_opt_by_nodes(route0, t1, t2, t3, t4):
    tour = _LinkedTour(route0)

    t1 = int(t1)
    t2 = int(t2)
    t3 = int(t3)
    t4 = int(t4)

    if int(tour.succ[t1]) != t2 and int(tour.succ[t2]) == t1:
        t1, t2 = t2, t1

    if int(tour.succ[t3]) != t4 and int(tour.succ[t4]) == t3:
        t3, t4 = t4, t3

    if int(tour.succ[t1]) != t2 or int(tour.succ[t3]) != t4:
        return route0.copy()

    try:
        tour.apply_two_opt_nodes(t1, t2, t3, t4)
    except Exception:
        return route0.copy()

    return tour.to_route(start = int(route0[0]))

def _lk_alternating_search(distance_matrix, route0, cand_arr, max_depth = 5, breadth = 5):
    n = route0.shape[0]
    succ, pred = _successor_predecessor_from_route(route0)
    best_route = route0
    best_gain = 0.0
    old_dist = _tour_distance_zero(distance_matrix, route0)

    for t1 in route0:
        for t2 in [succ[t1], pred[t1]]:
            gain_x1 = _edge_cost(distance_matrix, t1, t2)
            stack = []

            y_options = []
            used = set([int(t1), int(t2)])
            for c in cand_arr[int(t2)]:
                if c < 0:
                    continue
                t3 = int(c)
                if t3 in used:
                    continue
                if t3 == succ[t2] or t3 == pred[t2]:
                    continue

                gain = gain_x1 - _edge_cost(distance_matrix, t2, t3)
                if gain > 0.0:
                    y_options.append((gain, int(t3)))

            y_options = sorted(y_options, key = lambda x: -x[0])[:max(1, breadth)]
            for gain, t3 in y_options:
                stack.append((int(t1), int(t2), int(t3), gain, 1, set([int(t1), int(t2), int(t3)])))

            while len(stack) > 0:
                t1_, t2_, last, gain, depth, used_nodes = stack.pop()

                closing_gain = gain - _edge_cost(distance_matrix, last, t1_)
                if closing_gain > 0.0:
                    try:
                        candidate = _apply_two_opt_by_nodes(route0, t1_, t2_, last, succ[last])
                        cand_dist = _tour_distance_zero(distance_matrix, candidate)
                        real_gain = old_dist - cand_dist
                        if real_gain > best_gain + 1e-12 and _validate_route(_route_to_one(candidate), n):
                            best_gain = real_gain
                            best_route = candidate
                    except Exception:
                        pass

                if depth >= max_depth:
                    continue

                neighbors = [int(succ[last]), int(pred[last])]
                next_branches = []

                for t_next in neighbors:
                    if t_next in used_nodes:
                        continue

                    gain_after_delete = gain + _edge_cost(distance_matrix, last, t_next)
                    if gain_after_delete <= 0.0:
                        continue

                    for c in cand_arr[t_next]:
                        if c < 0:
                            continue
                        t_new = int(c)

                        if t_new in used_nodes:
                            continue
                        if t_new == succ[t_next] or t_new == pred[t_next]:
                            continue

                        new_gain = gain_after_delete - _edge_cost(distance_matrix, t_next, t_new)
                        if new_gain > 0.0:
                            next_branches.append((new_gain, t_next, t_new))

                level_breadth = max(1, breadth) if depth < 2 else 1
                next_branches = sorted(next_branches, key = lambda x: -x[0])[:level_breadth]

                for new_gain, t_next, t_new in next_branches:
                    new_used = set(used_nodes)
                    new_used.add(t_next)
                    new_used.add(t_new)
                    stack.append((t1_, t2_, t_new, new_gain, depth + 1, new_used))

    return best_route, float(best_gain)

############################################################################

def _segments_after_two_breaks(route0, i, j):
    n = route0.shape[0]

    if i > j:
        i, j = j, i

    if i == j:
        return None
    if (i + 1) % n == j:
        return None
    if i == 0 and j == n - 1:
        return None

    seg_a = route0[i + 1:j + 1]
    seg_b = np.concatenate((route0[j + 1:], route0[:i + 1]))

    if seg_a.shape[0] == 0 or seg_b.shape[0] == 0:
        return None

    return seg_a, seg_b

def _patch_two_fragments(distance_matrix, route0, i, j, old_distance = None):
    n = route0.shape[0]
    pieces = _segments_after_two_breaks(route0, i, j)

    if pieces is None:
        return route0, 0.0

    seg_a, seg_b = pieces
    if old_distance is None:
        old_distance = _tour_distance_zero(distance_matrix, route0)

    best_route = route0
    best_gain = 0.0

    orientations_a = [seg_a, seg_a[::-1].copy()]
    orientations_b = [seg_b, seg_b[::-1].copy()]

    for a in orientations_a:
        for b in orientations_b:
            candidate_routes = [
                np.concatenate((a, b)),
                np.concatenate((b, a))
            ]

            for cand in candidate_routes:
                if cand.shape[0] != n or len(set(cand.tolist())) != n:
                    continue

                new_distance = _tour_distance_zero(distance_matrix, cand)
                gain = old_distance - new_distance

                if gain > best_gain + 1e-12:
                    best_gain = gain
                    best_route = cand

    return best_route, float(best_gain)

def _patching_pass(distance_matrix, route0, cand_arr, max_trials_per_edge = 20):
    n = route0.shape[0]
    pos = _build_pos(route0)
    best_gain = 0.0
    best_route = route0
    old_distance = _tour_distance_zero(distance_matrix, route0)

    for i in range(n):
        b = int(route0[(i + 1) % n])
        trials = 0

        for c in cand_arr[b]:
            if c < 0:
                continue
            if trials >= max_trials_per_edge:
                break

            j = pos[int(c)]

            if j == i or j == (i + 1) % n or (j + 1) % n == i:
                continue

            ii, jj = i, j
            if ii > jj:
                ii, jj = jj, ii

            if ii == 0 and jj == n - 1:
                continue

            cand, gain = _patch_two_fragments(distance_matrix, route0, ii, jj, old_distance = old_distance)
            trials = trials + 1

            if gain > best_gain + 1e-12:
                best_gain = gain
                best_route = cand

    return best_route, float(best_gain)

############################################################################

def _restricted_three_opt_pass(distance_matrix, route0, candidates, max_trials = 5000):
    n = route0.shape[0]
    best_delta = 0.0
    best_route = route0
    trials = 0
    pos = _build_pos(route0)
    old_distance = _tour_distance_zero(distance_matrix, route0)

    for i in range(0, n):
        if trials >= max_trials:
            break

        a = int(route0[i])
        b = int(route0[(i + 1) % n])
        candidate_nodes = candidates[a] + candidates[b]

        for c0 in candidate_nodes:
            if trials >= max_trials:
                break

            j = pos[int(c0)]

            if j == i or j == (i + 1) % n or (j + 1) % n == i:
                continue

            for e0 in candidates[int(c0)]:
                if trials >= max_trials:
                    break

                k = pos[int(e0)]
                idx = sorted([i, j, k])
                p, q, r = idx

                if len(set(idx)) < 3:
                    continue
                if p == 0 and r == n - 1:
                    continue

                trials = trials + 1

                A = route0[:p + 1]
                B = route0[p + 1:q + 1]
                C = route0[q + 1:r + 1]
                D = route0[r + 1:]

                variants = [
                    np.concatenate((A, B[::-1], C, D)),
                    np.concatenate((A, B, C[::-1], D)),
                    np.concatenate((A, B[::-1], C[::-1], D)),
                    np.concatenate((A, C, B, D)),
                    np.concatenate((A, C[::-1], B, D)),
                    np.concatenate((A, C, B[::-1], D)),
                    np.concatenate((A, C[::-1], B[::-1], D))
                ]

                for candidate_route in variants:
                    if candidate_route.shape[0] != n or len(set(candidate_route.tolist())) != n:
                        continue

                    new_distance = _tour_distance_zero(distance_matrix, candidate_route)
                    delta = new_distance - old_distance

                    if delta < best_delta:
                        best_delta = delta
                        best_route = candidate_route

    return best_route, float(-best_delta)

############################################################################

def _double_bridge(route0, rng):
    n = route0.shape[0]

    if n < 8:
        return route0.copy()

    cuts = sorted(rng.sample(range(1, n), 4))
    a, b, c, d = cuts

    p1 = route0[:a]
    p2 = route0[a:b]
    p3 = route0[b:c]
    p4 = route0[c:d]
    p5 = route0[d:]

    return np.concatenate((p1, p3, p2, p4, p5))

def _kick(route0, rng, kicks = 1):
    new_route = route0.copy()
    for _ in range(0, max(1, kicks)):
        new_route = _double_bridge(new_route, rng)
    return new_route


############################################################################

def _edge_key(a, b):
    a = int(a)
    b = int(b)
    return (a, b) if a < b else (b, a)

def _build_edge_set_from_route(route0):
    n = route0.shape[0]
    edges = set()
    for i in range(n):
        a = int(route0[i])
        b = int(route0[(i + 1) % n])
        edges.add(_edge_key(a, b))
    return edges

def _rebuild_tour_from_edges(n, edge_set, start = 0):
    if len(edge_set) != n:
        return None

    adj = [[] for _ in range(n)]

    for a, b in edge_set:
        adj[a].append(b)
        adj[b].append(a)

    for i in range(n):
        if len(adj[i]) != 2:
            return None

    route = [start]
    prev = -1
    cur = start

    for _ in range(n - 1):
        nxts = adj[cur]
        nxt = nxts[0] if nxts[0] != prev else nxts[1]
        if nxt == start:
            return None
        route.append(nxt)
        prev, cur = cur, nxt

    if start not in adj[cur]:
        return None

    if len(set(route)) != n:
        return None

    return np.array(route, dtype = np.int64)

def _apply_edge_exchange(route0, removed_edges, added_edges):
    n = route0.shape[0]
    edge_set = _build_edge_set_from_route(route0)

    for e in removed_edges:
        ek = _edge_key(e[0], e[1])
        if ek not in edge_set:
            return None
        edge_set.remove(ek)

    for e in added_edges:
        ek = _edge_key(e[0], e[1])
        if ek in edge_set:
            return None
        edge_set.add(ek)

    return _rebuild_tour_from_edges(n, edge_set, start = int(route0[0]))

def _is_tour_edge(succ, pred, a, b):
    return int(succ[a]) == int(b) or int(pred[a]) == int(b)

def _orient_tour_edge_from_linked(tour, a, b):
    a = int(a)
    b = int(b)

    if int(tour.succ[a]) == b:
        return a, b
    if int(tour.succ[b]) == a:
        return b, a
    return None

def _two_opt_gain(distance_matrix, a, b, c, d):
    a = int(a)
    b = int(b)
    c = int(c)
    d = int(d)
    return float(distance_matrix[a, b] + distance_matrix[c, d] - distance_matrix[b, c] - distance_matrix[d, a])

def _sequential_linked_lk_search(distance_matrix, route0, cand_arr, max_depth = 5, breadth = 5, min_gain = 1e-12):
    base_tour = _LinkedTour(route0)
    base_distance = _tour_distance_zero(distance_matrix, route0)
    best_gain = 0.0
    best_route = route0

    def expand(tour, anchor, tail, current_distance, depth, used_nodes):
        nonlocal best_gain, best_route

        edge_anchor = _orient_tour_edge_from_linked(tour, anchor, tail)
        if edge_anchor is None:
            return

        a, b = edge_anchor
        options = []

        for c in cand_arr[int(tail)]:
            if c < 0:
                continue
            t3 = int(c)

            if t3 == anchor or t3 in used_nodes:
                continue
            if int(tour.succ[tail]) == t3 or int(tour.pred[tail]) == t3:
                continue

            for t4 in tour.neighbors(t3):
                t4 = int(t4)

                if t4 == tail or t4 == anchor:
                    continue
                if t4 in used_nodes:
                    continue

                edge_other = _orient_tour_edge_from_linked(tour, t3, t4)
                if edge_other is None:
                    continue

                c0, d0 = edge_other
                delta = _two_opt_gain(distance_matrix, a, b, c0, d0)

                if delta <= min_gain:
                    continue

                options.append((delta, t3, t4, a, b, c0, d0))

        if len(options) == 0:
            return

        level_breadth = max(1, breadth) if depth <= 2 else 1
        options = sorted(options, key = lambda x: -x[0])[:level_breadth]

        for delta, t3, t4, a0, b0, c0, d0 in options:
            new_tour = tour.clone()
            try:
                new_tour.apply_two_opt_nodes(a0, b0, c0, d0)
            except Exception:
                continue

            new_distance = current_distance - float(delta)
            total_gain = base_distance - new_distance

            if total_gain > best_gain + min_gain:
                cand_route = new_tour.to_route(start = int(route0[0]))
                if _validate_route(_route_to_one(cand_route), route0.shape[0]):
                    best_gain = total_gain
                    best_route = cand_route

            if depth < max_depth:
                new_used = set(used_nodes)
                new_used.add(int(tail))
                new_used.add(int(t3))
                new_used.add(int(t4))
                expand(new_tour, anchor, t4, new_distance, depth + 1, new_used)

    for t1 in route0:
        t1 = int(t1)
        for t2 in base_tour.neighbors(t1):
            t2 = int(t2)
            expand(base_tour.clone(), t1, t2, base_distance, 1, set([t1, t2]))

    return best_route, float(best_gain)

def _explicit_lk_kopt_search(distance_matrix, route0, cand_arr, max_depth = 5, breadth = 6, min_gain = 1e-12):

    succ, pred = _successor_predecessor_from_route(route0)
    base_distance = _tour_distance_zero(distance_matrix, route0)

    best_gain = 0.0
    best_route = route0

    for t1 in route0:
        t1 = int(t1)

        for t2 in [int(succ[t1]), int(pred[t1])]:
            removed = [(_edge_key(t1, t2))]
            added = []
            gain = _edge_cost(distance_matrix, t1, t2)
            used_nodes = set([t1, t2])

            stack = [(t2, gain, removed, added, used_nodes, 1)]

            while len(stack) > 0:
                tail, gain_so_far, removed_edges, added_edges, used, depth = stack.pop()
                add_options = []

                for c in cand_arr[tail]:
                    if c < 0:
                        continue

                    t_new = int(c)

                    if t_new == t1 and depth < 2:
                        continue
                    if t_new in used and t_new != t1:
                        continue
                    if _is_tour_edge(succ, pred, tail, t_new):
                        continue

                    add_gain = gain_so_far - _edge_cost(distance_matrix, tail, t_new)

                    if t_new == t1:
                        if add_gain > 0.0:
                            candidate = _apply_edge_exchange(route0, removed_edges, added_edges + [_edge_key(tail, t1)])
                            if candidate is not None:
                                cand_distance = _tour_distance_zero(distance_matrix, candidate)
                                real_gain = base_distance - cand_distance
                                if real_gain > best_gain + min_gain:
                                    best_gain = real_gain
                                    best_route = candidate
                        continue

                    if add_gain > 0.0:
                        add_options.append((add_gain, t_new))

                level_breadth = max(1, breadth) if depth <= 2 else 1
                add_options = sorted(add_options, key = lambda x: -x[0])[:level_breadth]

                for add_gain, t_new in add_options:
                    new_added = added_edges + [_edge_key(tail, t_new)]
                    delete_options = []

                    for t_next in [int(succ[t_new]), int(pred[t_new])]:
                        if t_next in used:
                            continue

                        e_del = _edge_key(t_new, t_next)
                        if e_del in removed_edges:
                            continue

                        del_gain = add_gain + _edge_cost(distance_matrix, t_new, t_next)

                        close_gain = del_gain - _edge_cost(distance_matrix, t_next, t1)
                        if close_gain > 0.0:
                            candidate = _apply_edge_exchange(
                                route0,
                                removed_edges + [e_del],
                                new_added + [_edge_key(t_next, t1)]
                            )
                            if candidate is not None:
                                cand_distance = _tour_distance_zero(distance_matrix, candidate)
                                real_gain = base_distance - cand_distance
                                if real_gain > best_gain + min_gain:
                                    best_gain = real_gain
                                    best_route = candidate

                        if depth < max_depth and del_gain > 0.0:
                            delete_options.append((del_gain, t_next, e_del))

                    level_breadth = max(1, breadth) if depth <= 2 else 1
                    delete_options = sorted(delete_options, key = lambda x: -x[0])[:level_breadth]

                    for del_gain, t_next, e_del in delete_options:
                        new_used = set(used)
                        new_used.add(t_new)
                        new_used.add(t_next)
                        stack.append((
                            t_next,
                            del_gain,
                            removed_edges + [e_del],
                            new_added,
                            new_used,
                            depth + 1
                        ))

    return best_route, float(best_gain)


############################################################################

def local_search_lkh_strong(distance_matrix, city_tour, candidate_size = 20, alpha_candidates = True, ascent_iterations = 100, max_depth = 5, breadth = 5, patching = True, patching_trials = 20, three_opt = True, three_opt_trials = 5000, max_passes = 50, candidates_cache = None, verbose = True, use_dont_look_bits = True):
    distance_matrix = np.ascontiguousarray(np.array(distance_matrix, dtype = np.float64))
    n = distance_matrix.shape[0]

    if isinstance(city_tour[0], np.ndarray):
        route0 = city_tour[0].astype(np.int64)
        if np.min(route0) >= 1:
            route0 = route0 - 1
    else:
        route0 = _route_to_zero(city_tour[0])

    if route0.shape[0] != n:
        route0 = route0[:n]

    if not _validate_route(_route_to_one(route0), n):
        raise ValueError('city_tour must contain a valid 1-indexed closed route or a zero-indexed numpy route')

    if candidates_cache is None:
        if alpha_candidates == True:
            candidates, alpha, pi, one_tree_edges, lb = _alpha_nearness_candidates(
                distance_matrix,
                candidate_size = candidate_size,
                ascent_iterations = ascent_iterations,
                root = 0,
                extra_nearest = True
            )
        else:
            candidates = _nearest_candidates(distance_matrix, candidate_size = candidate_size)
        candidates = _make_candidate_sets_symmetric(candidates, candidate_size, distance_matrix = distance_matrix)
    else:
        candidates = _make_candidate_sets_symmetric(candidates_cache, candidate_size, distance_matrix = distance_matrix)

    cand_arr = _candidate_array(candidates)

    distance = _tour_distance_zero(distance_matrix, route0)

    for it in range(max(1, max_passes)):
        if verbose == True:
            print('Iteration = ', it, 'Distance = ', round(distance, 2))

        improved = False

        # Fast 2-opt intensification.
        new_route, new_distance = _intensify_2opt(
            distance_matrix,
            route0,
            cand_arr,
            max_passes = 100,
            use_dont_look_bits = use_dont_look_bits
        )

        if new_distance < distance - 1e-12:
            route0 = new_route
            distance = new_distance
            improved = True

        # Sequential linked-tour LK-style search.
        new_route, gain = _sequential_linked_lk_search(
            distance_matrix,
            route0,
            cand_arr,
            max_depth = max_depth,
            breadth = breadth
        )

        if gain > 1e-12:
            route0 = new_route
            distance = _tour_distance_zero(distance_matrix, route0)
            improved = True

        # Edge-set fallback search retained for compatibility on cases where
        # the linked sequential core does not find an improving chain.
        new_route, gain = _explicit_lk_kopt_search(
            distance_matrix,
            route0,
            cand_arr,
            max_depth = max_depth,
            breadth = breadth
        )

        if gain > 1e-12:
            route0 = new_route
            distance = _tour_distance_zero(distance_matrix, route0)
            improved = True

        # Fallback practical alternating-edge LK search.
        new_route, gain = _lk_alternating_search(
            distance_matrix,
            route0,
            cand_arr,
            max_depth = max_depth,
            breadth = breadth
        )

        if gain > 1e-12:
            route0 = new_route
            distance = _tour_distance_zero(distance_matrix, route0)
            improved = True

        # Limited patching.
        if patching == True:
            new_route, gain = _patching_pass(
                distance_matrix,
                route0,
                cand_arr,
                max_trials_per_edge = patching_trials
            )

            if gain > 1e-12:
                route0 = new_route
                distance = _tour_distance_zero(distance_matrix, route0)
                improved = True

        # Restricted 3-opt.
        if three_opt == True:
            new_route, gain = _restricted_three_opt_pass(
                distance_matrix,
                route0,
                candidates,
                max_trials = three_opt_trials
            )

            if gain > 1e-12:
                route0 = new_route
                distance = _tour_distance_zero(distance_matrix, route0)
                improved = True

        if improved == False:
            break

    route = _close_route(_route_to_one(route0))
    distance = distance_calc(distance_matrix, [route, 0])

    return route, distance

############################################################################

def lin_kernighan_helsgaun(distance_matrix, city_tour = None, initial_location = -1, candidate_size = 20, alpha_candidates = True, ascent_iterations = 100, max_depth = 5, breadth = 5, patching = True, patching_trials = 20, restarts = 10, kicks = 1, three_opt = True, three_opt_trials = 5000, max_passes = 50, elite_candidates = True, seed = None, verbose = True, use_dont_look_bits = True):

    distance_matrix = np.ascontiguousarray(np.array(distance_matrix, dtype = np.float64))

    if distance_matrix.ndim != 2 or distance_matrix.shape[0] != distance_matrix.shape[1]:
        raise ValueError('distance_matrix must be a square matrix')

    if np.any(distance_matrix < 0):
        raise ValueError('distance_matrix cannot contain negative distances')

    n = distance_matrix.shape[0]
    rng = random.Random(seed)

    alpha = None
    if alpha_candidates == True:
        candidates, alpha, pi, one_tree_edges, lb = _alpha_nearness_candidates(
            distance_matrix,
            candidate_size = candidate_size,
            ascent_iterations = ascent_iterations,
            root = 0,
            extra_nearest = True
        )
    else:
        candidates = _nearest_candidates(distance_matrix, candidate_size = candidate_size)

    candidates = _make_candidate_sets_symmetric(candidates, candidate_size, distance_matrix = distance_matrix)

    if city_tour is None:
        if alpha_candidates == True:
            route0, distance = _alpha_greedy_solution(
                distance_matrix,
                candidates,
                alpha = alpha,
                initial_location = initial_location,
                rng = rng
            )
        else:
            route0, distance = _nearest_neighbour_solution(
                distance_matrix,
                initial_location = initial_location,
                random_start = False,
                rng = rng
            )
        route = _close_route(_route_to_one(route0))
        city_tour = [route, distance]
    else:
        route = _close_route(_normalize_route(city_tour[0]))
        distance = float(city_tour[1])
        if distance <= 0:
            distance = distance_calc(distance_matrix, [route, 0])
        city_tour = [route, distance]

    route, distance = local_search_lkh_strong(
        distance_matrix,
        city_tour,
        candidate_size = candidate_size,
        alpha_candidates = alpha_candidates,
        ascent_iterations = ascent_iterations,
        max_depth = max_depth,
        breadth = breadth,
        patching = patching,
        patching_trials = patching_trials,
        three_opt = three_opt,
        three_opt_trials = three_opt_trials,
        max_passes = max_passes,
        candidates_cache = candidates,
        verbose = False,
        use_dont_look_bits = use_dont_look_bits
    )

    best_route = copy.deepcopy(route)
    best_distance = float(distance)

    best_route0 = _route_to_zero(best_route)
    if elite_candidates == True:
        candidates = _augment_candidates_with_route(candidates, best_route0, candidate_size, distance_matrix = distance_matrix)
    cand_arr = _candidate_array(candidates)

    if verbose == True:
        print('Iteration = ', 0, 'Distance = ', round(best_distance, 2))

    for r in range(1, max(1, restarts) + 1):
        if r % 3 == 0:
            seed_route0, seed_distance = _randomized_greedy_solution(
                distance_matrix,
                candidate_size = min(5, max(1, n - 1)),
                rng = rng
            )
        else:
            seed_route0 = _route_to_zero(best_route)
            seed_route0 = _kick(seed_route0, rng, kicks = kicks)
            seed_distance = _tour_distance_zero(distance_matrix, seed_route0)

        seed_route = _close_route(_route_to_one(seed_route0))

        route, distance = local_search_lkh_strong(
            distance_matrix,
            [seed_route, seed_distance],
            candidate_size = candidate_size,
            alpha_candidates = alpha_candidates,
            ascent_iterations = ascent_iterations,
            max_depth = max_depth,
            breadth = breadth,
            patching = patching,
            patching_trials = patching_trials,
            three_opt = three_opt,
            three_opt_trials = three_opt_trials,
            max_passes = max_passes,
            candidates_cache = candidates,
            verbose = False
        )

        if distance < best_distance:
            best_route = copy.deepcopy(route)
            best_distance = float(distance)

            best_route0 = _route_to_zero(best_route)
            if elite_candidates == True:
                candidates = _augment_candidates_with_route(candidates, best_route0, candidate_size, distance_matrix = distance_matrix)

        if verbose == True:
            print('Iteration = ', r, 'Distance = ', round(best_distance, 2))

    return best_route, best_distance

############################################################################