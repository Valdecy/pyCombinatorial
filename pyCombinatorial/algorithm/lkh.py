############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email: valdecy.pereira@gmail.com
# Lesson: Lin-Kernighan-Helsgaun - Faithful Pure-Python Implementation

# Improvements over the inspired version:
#   1) O(n^2) alpha-nearness candidates (per-source DFS on the 1-tree topology
#      instead of an O(n) max-edge query per pair).
#   2) Faithful sequential k-opt search (k up to 5) with the proper LK gain
#      criterion: closing edge tested first at every depth, partial-sum gain
#      criterion (not per-step gain), edge-uniqueness enforced, feasibility
#      checked via single-cycle reconstruction.
#   3) Don't-look bits applied at the k-opt level (not only inside 2-opt).
#      Affected nodes are cleared after every applied move.

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
#  BASIC ROUTE / DISTANCE UTILITIES
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
#  SUCCESSOR / PREDECESSOR ARRAYS  (NUMBA ACCELERATED)
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

def _route_and_pos_from_successor(succ, start = 0):
    route = _route_from_successor(succ, start = start)
    pos = np.empty(route.shape[0], dtype = np.int64)
    for i in range(route.shape[0]):
        pos[int(route[i])] = i
    return route, pos

############################################################################
#  DOUBLY LINKED TOUR  (segment-aware 2-opt reversal)
############################################################################

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
        a = int(a); b = int(b); c = int(c); d = int(d)
        if int(self.succ[a]) != b or int(self.succ[c]) != d:
            raise ValueError('2-opt move expects directed tour edges (a,b) and (c,d)')
        seg_len = _path_length_successor(self.succ, b, c)
        comp_len = self.n - seg_len
        if seg_len <= comp_len:
            _reverse_path_in_successor(self.succ, self.pred, b, c)
            self.succ[a] = c; self.pred[c] = a
            self.succ[b] = d; self.pred[d] = b
        else:
            _reverse_path_in_successor(self.succ, self.pred, d, a)
            self.succ[c] = a; self.pred[a] = c
            self.succ[d] = b; self.pred[b] = d
        self.start = a

@njit(cache = False)
def _reverse_segment_in_route_numba(route0, i, j):
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
#  MINIMUM 1-TREE  +  HELD-KARP SUBGRADIENT ASCENT
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

    lower_bound = weighted_cost - 2.0 * np.sum(pi)
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
            direction = g + beta * (g - prev_g)
            dir_norm = float(np.dot(direction, direction))
            if dir_norm <= 1e-12:
                direction = g
                dir_norm = norm

            step = step_scale / np.sqrt(dir_norm)
            pi = pi + step * direction
            pi = pi - np.mean(pi)
            prev_g = g
            t = t + 1

        step_scale = 0.5 * step_scale
        period = max(2, period // 2)

    return best_pi, best_edges, best_degree, best_lb

############################################################################
#  IMPROVEMENT 1 :  O(n^2) ALPHA-NEARNESS
#  -------------------------------------------------------------------------
#  Old version did an O(n) DFS per pair  =>  O(n^3).
#  New version: one DFS per source node on the MST topology of the 1-tree
#  (MST excluding the special root). beta[i, *] is filled in O(n) per source,
#  so the full beta matrix is O(n^2). Alpha is then computed in O(n^2).
############################################################################

def _build_mst_adjacency_no_root(n, one_tree_edges, weighted, root):
    adj = [[] for _ in range(n)]
    for i, j in one_tree_edges:
        if i == root or j == root:
            continue
        w = float(weighted[i, j])
        adj[i].append((j, w))
        adj[j].append((i, w))
    return adj

def _compute_beta_matrix(n, mst_adj, root):
    """beta[i, j] = max edge weight on the unique i->j path in the MST
    spanning the n - 1 non-root nodes. Computed in O(n^2) with a single
    DFS per source."""
    beta = np.zeros((n, n), dtype = float)
    for source in range(n):
        if source == root:
            continue
        stack = [(source, -1, 0.0)]
        visited = np.zeros(n, dtype = bool)
        visited[source] = True
        while len(stack) > 0:
            v, parent, max_e = stack.pop()
            for u, w in mst_adj[v]:
                if not visited[u]:
                    visited[u] = True
                    new_max = max_e if max_e > w else w
                    beta[source, u] = new_max
                    stack.append((u, v, new_max))
    return beta

def _exact_alpha_values_fast(distance_matrix, pi, one_tree_edges, root = 0):
    n = distance_matrix.shape[0]
    weighted = distance_matrix + pi.reshape((n, 1)) + pi.reshape((1, n))
    tree_set = set((min(i, j), max(i, j)) for i, j in one_tree_edges)

    mst_adj = _build_mst_adjacency_no_root(n, one_tree_edges, weighted, root)
    beta = _compute_beta_matrix(n, mst_adj, root)

    root_edges_sorted = sorted(
        [(weighted[root, j], root, j) for j in range(n) if j != root],
        key = lambda x: x[0]
    )
    selected_root_targets = {root_edges_sorted[0][2], root_edges_sorted[1][2]}
    second_root_weight = root_edges_sorted[1][0]

    alpha = np.zeros((n, n), dtype = float)
    for i in range(n):
        for j in range(i + 1, n):
            a, b = i, j
            if (a, b) in tree_set:
                val = 0.0
            elif i == root or j == root:
                other = j if i == root else i
                if other in selected_root_targets:
                    val = 0.0
                else:
                    val = float(weighted[root, other] - second_root_weight)
            else:
                max_w = float(beta[i, j])
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

    alpha = _exact_alpha_values_fast(distance_matrix, pi, one_tree_edges, root = root)

    candidates = []
    for i in range(n):
        scored = []
        for j in range(n):
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
    for i in range(n):
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
    for i in range(n):
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
#  INITIAL SOLUTIONS
############################################################################

def _nearest_neighbour_solution(distance_matrix, initial_location = -1, random_start = False, rng = None):
    n = distance_matrix.shape[0]
    if rng is None:
        rng = random.Random(None)
    if random_start == True:
        start = rng.randrange(n)
    else:
        start = 0 if initial_location == -1 else max(0, min(n - 1, int(initial_location) - 1))
    unvisited = set(range(n))
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
    unvisited = set(range(n))
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
    unvisited = set(range(n))
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
#  FAST 2-OPT  (don't-look bits, segment-aware reversal)
############################################################################

@njit(cache = False)
def _positions_numba(route0):
    n = route0.shape[0]
    pos = np.empty(n, dtype = np.int64)
    for i in range(n):
        pos[route0[i]] = i
    return pos

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
                        for node in (a0, b0, c0, d0):
                            dlb[node] = 0
                            dlb[int(tour.pred[node])] = 0
                            dlb[int(tour.succ[node])] = 0
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
#  IMPROVEMENT 2 :  FAITHFUL SEQUENTIAL k-OPT  (LK gain criterion)
#  -------------------------------------------------------------------------
#  Recursive descent that builds a chain (t_1, t_2, ..., t_{2k}) where:
#     x_i = (t_{2i-1}, t_{2i})  are removed tour edges
#     y_i = (t_{2i},   t_{2i+1}) are added candidate edges
#  At every level >= 2 we test the *closing* move first (replacing y_k with
#  (t_{2k}, t_1)). The LK partial-sum gain criterion
#       sum_{j=1..i} c(x_j) - sum_{j=1..i} c(y_j) > 0
#  is enforced before we descend deeper. Feasibility (single Hamiltonian
#  cycle) is checked by reconstructing the tour from the symmetric edge
#  difference whenever we attempt a close.
############################################################################

def _build_edge_set_from_route(route0):
    n = route0.shape[0]
    edges = set()
    for i in range(n):
        a = int(route0[i])
        b = int(route0[(i + 1) % n])
        edges.add((a, b) if a < b else (b, a))
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

def _apply_sequential_chain(route0, chain):
    """Apply a sequential k-opt move described by chain = [t_1, t_2, ..., t_{2k}].
    Edges x_i = (t_{2i-1}, t_{2i}) are removed, edges y_i = (t_{2i}, t_{2i+1})
    are added for i = 1..k-1, and the move is closed with y_k = (t_{2k}, t_1).
    Returns the resulting route as a numpy array, or None if the move does
    not produce a valid single Hamiltonian cycle."""
    n = route0.shape[0]
    k = len(chain) // 2
    if 2 * k != len(chain) or k < 2:
        return None

    edges = _build_edge_set_from_route(route0)

    # Remove x_i edges
    for i in range(k):
        a = int(chain[2 * i])
        b = int(chain[2 * i + 1])
        e = (a, b) if a < b else (b, a)
        if e not in edges:
            return None
        edges.remove(e)

    # Add y_i edges (i = 1..k-1)
    for i in range(k - 1):
        a = int(chain[2 * i + 1])
        b = int(chain[2 * i + 2])
        e = (a, b) if a < b else (b, a)
        if e in edges:
            return None
        edges.add(e)

    # Closing y_k
    a = int(chain[-1])
    b = int(chain[0])
    e = (a, b) if a < b else (b, a)
    if e in edges:
        return None
    edges.add(e)

    return _rebuild_tour_from_edges(n, edges, start = int(route0[0]))

def _lk_sequential_search_from(distance_matrix, route0, succ, pred, cand_arr, t1, max_depth, breadth):
    """Run the faithful sequential k-opt search starting from a single t_1.
    Returns (best_route, best_gain, best_chain) — the best improving chain
    rooted at t_1 across both directions (succ, pred) and all depths up to
    max_depth. If no improvement, gain == 0.0 and chain is None."""
    n = route0.shape[0]
    base_distance = _tour_distance_zero(distance_matrix, route0)

    state = {
        'best_gain':  0.0,
        'best_route': route0,
        'best_chain': None
    }

    def search(chain, chain_set, C_X, C_Y, level):
        t_last = chain[-1]

        # ---- closing test (tested FIRST at every depth >= 2) ----
        if level >= 2:
            close_cost = float(distance_matrix[t_last, t1])
            gain_close = C_X - C_Y - close_cost
            if gain_close > state['best_gain'] + 1e-12:
                cand_route = _apply_sequential_chain(route0, chain)
                if cand_route is not None:
                    cand_dist = _tour_distance_zero(distance_matrix, cand_route)
                    real_gain = base_distance - cand_dist
                    if real_gain > state['best_gain'] + 1e-12:
                        state['best_gain']  = real_gain
                        state['best_route'] = cand_route
                        state['best_chain'] = list(chain)

        if level >= max_depth:
            return

        # ---- candidate y-additions (LK gain criterion) ----
        candidates_pool = []
        for c in cand_arr[t_last]:
            if c < 0:
                continue
            t_new = int(c)
            if t_new == t1 or t_new in chain_set:
                continue
            # y must not be the current tour edge at t_last
            if t_new == int(succ[t_last]) or t_new == int(pred[t_last]):
                continue

            c_y = float(distance_matrix[t_last, t_new])
            G   = C_X - C_Y - c_y                 # partial-sum gain after y_level
            if G <= 1e-12:                        # LK criterion: must stay positive
                continue
            candidates_pool.append((G, t_new, c_y))

        candidates_pool.sort(key = lambda x: -x[0])
        # Helsgaun: full breadth at the first two levels, contracts deeper.
        level_breadth = breadth if level <= 2 else max(1, breadth - level + 1)
        candidates_pool = candidates_pool[:level_breadth]

        for G, t_new, c_y in candidates_pool:
            for t_partner in (int(succ[t_new]), int(pred[t_new])):
                if t_partner == t1 or t_partner in chain_set:
                    continue
                c_x = float(distance_matrix[t_new, t_partner])

                chain.append(t_new)
                chain.append(t_partner)
                chain_set.add(t_new)
                chain_set.add(t_partner)
                search(chain, chain_set, C_X + c_x, C_Y + c_y, level + 1)
                chain_set.discard(t_partner)
                chain_set.discard(t_new)
                chain.pop()
                chain.pop()

    for t2 in (int(succ[t1]), int(pred[t1])):
        c_x1 = float(distance_matrix[t1, t2])
        chain = [t1, t2]
        chain_set = {t1, t2}
        search(chain, chain_set, c_x1, 0.0, 1)

    return state['best_route'], state['best_gain'], state['best_chain']

def _lk_intensify(distance_matrix, route0, cand_arr, max_depth = 5, breadth = 5, max_outer = 1000):
    """Outer loop of the faithful LK search with don't-look bits.
    Each pass scans every node t_1 in turn; whenever an improving move is
    found from a given t_1, the move is applied and don't-look bits are
    cleared for all nodes touched by the chain (and their new neighbours).
    Stops when a full pass finds no improvement."""
    n = route0.shape[0]
    route0 = route0.copy()
    distance = _tour_distance_zero(distance_matrix, route0)
    succ, pred = _successor_predecessor_from_route(route0)
    dlb = np.zeros(n, dtype = np.uint8)

    for _ in range(max_outer):
        improved_in_pass = False

        for t1 in range(n):
            if dlb[t1] == 1:
                continue

            new_route, gain, chain = _lk_sequential_search_from(
                distance_matrix, route0, succ, pred, cand_arr,
                t1, max_depth, breadth
            )

            if gain > 1e-12 and chain is not None:
                affected = set(chain)
                new_succ, new_pred = _successor_predecessor_from_route(new_route)
                for node in list(affected):
                    affected.add(int(new_succ[node]))
                    affected.add(int(new_pred[node]))
                for node in affected:
                    dlb[node] = 0

                route0   = new_route
                succ     = new_succ
                pred     = new_pred
                distance = distance - gain
                improved_in_pass = True
            else:
                dlb[t1] = 1

        if improved_in_pass == False:
            break

    return route0, float(distance)

############################################################################
#  PATCHING  (handles non-sequential moves)
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
    best_gain  = 0.0
    orientations_a = [seg_a, seg_a[::-1].copy()]
    orientations_b = [seg_b, seg_b[::-1].copy()]

    for a in orientations_a:
        for b in orientations_b:
            for cand in (np.concatenate((a, b)), np.concatenate((b, a))):
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
    pos = {int(route0[i]): i for i in range(n)}
    best_gain  = 0.0
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
            ii, jj = (i, j) if i < j else (j, i)
            if ii == 0 and jj == n - 1:
                continue
            cand, gain = _patch_two_fragments(distance_matrix, route0, ii, jj, old_distance = old_distance)
            trials = trials + 1
            if gain > best_gain + 1e-12:
                best_gain = gain
                best_route = cand
    return best_route, float(best_gain)

############################################################################
#  RESTRICTED 3-OPT
############################################################################

def _restricted_three_opt_pass(distance_matrix, route0, candidates, max_trials = 5000):
    n = route0.shape[0]
    best_delta = 0.0
    best_route = route0
    trials = 0
    pos = {int(route0[i]): i for i in range(n)}
    old_distance = _tour_distance_zero(distance_matrix, route0)

    for i in range(n):
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
#  DOUBLE-BRIDGE PERTURBATION
############################################################################

def _double_bridge(route0, rng):
    n = route0.shape[0]
    if n < 8:
        return route0.copy()
    cuts = sorted(rng.sample(range(1, n), 4))
    a, b, c, d = cuts
    p1 = route0[:a]; p2 = route0[a:b]; p3 = route0[b:c]; p4 = route0[c:d]; p5 = route0[d:]
    return np.concatenate((p1, p3, p2, p4, p5))

def _kick(route0, rng, kicks = 1):
    new_route = route0.copy()
    for _ in range(max(1, kicks)):
        new_route = _double_bridge(new_route, rng)
    return new_route

############################################################################
#  LOCAL SEARCH ENGINE (faithful version)
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

        # ---- fast 2-opt with DLB ----
        new_route, new_distance = _intensify_2opt(
            distance_matrix, route0, cand_arr,
            max_passes = 100, use_dont_look_bits = use_dont_look_bits
        )
        if new_distance < distance - 1e-12:
            route0 = new_route
            distance = new_distance
            improved = True

        # ---- faithful sequential k-opt (LK gain criterion, DLB) ----
        new_route, new_distance = _lk_intensify(
            distance_matrix, route0, cand_arr,
            max_depth = max_depth, breadth = breadth, max_outer = 1000
        )
        if new_distance < distance - 1e-12:
            route0 = new_route
            distance = new_distance
            improved = True

        # ---- patching for non-sequential improvements ----
        if patching == True:
            new_route, gain = _patching_pass(
                distance_matrix, route0, cand_arr,
                max_trials_per_edge = patching_trials
            )
            if gain > 1e-12:
                route0 = new_route
                distance = _tour_distance_zero(distance_matrix, route0)
                improved = True

        # ---- restricted 3-opt ----
        if three_opt == True:
            new_route, gain = _restricted_three_opt_pass(
                distance_matrix, route0, candidates,
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
#  MAIN ENTRY POINT
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
                distance_matrix, candidates, alpha = alpha,
                initial_location = initial_location, rng = rng
            )
        else:
            route0, distance = _nearest_neighbour_solution(
                distance_matrix, initial_location = initial_location,
                random_start = False, rng = rng
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
        distance_matrix, city_tour,
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
            distance_matrix, [seed_route, seed_distance],
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
