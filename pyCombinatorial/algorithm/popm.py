############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: POPMUSIC (Partial OPtimization Metaheuristic Under Special
#         Intensification Conditions) for the TSP

# GitHub Repository: <https://github.com/Valdecy>

# Algorithm based on:
#   E. D. Taillard and K. Helsgaun, "POPMUSIC for the Travelling Salesman
#   Problem", European Journal of Operational Research, 272(2):420-429
#   (2019). DOI: 10.1016/j.ejor.2018.06.039


############################################################################

# Required Libraries
import random
import numpy as np

############################################################################

# Function: Tour Distance (same signature as the rest of pyCombinatorial)
def distance_calc(distance_matrix, city_tour):
    distance = 0
    for k in range(0, len(city_tour[0]) - 1):
        m        = k + 1
        distance = distance + distance_matrix[city_tour[0][k] - 1, city_tour[0][m] - 1]
    return distance

############################################################################

# Function: Cost of a closed tour given as a list of 0-indexed cities with
#           tour[0] == tour[-1].
def _tour_cost(distance_matrix, tour):
    cost = 0.0
    for k in range(0, len(tour) - 1):
        cost = cost + distance_matrix[tour[k], tour[k + 1]]
    return float(cost)

############################################################################

def _path_three_opt(dist, n_path, max_neighbors, trials_param, rng, fixed_pair):
    N         = n_path + 1                                               
    tour      = list(range(N))                                              
    pos       = list(range(N))                                               
    best_tour = list(tour)

    # Initial cycle length.
    tour_length      = 0.0
    for i in range(0, N - 1):
        tour_length  = tour_length + dist[tour[i], tour[i + 1]]
    tour_length      = tour_length + dist[tour[N - 1], tour[0]]
    best_tour_length = tour_length

    # Build neighbor lists (sorted by distance), excluding self.
    k_neighbors = min(max_neighbors, N - 1)
    neighbor    = [None] * N
    for i in range(0, N):
        d_row       = dist[i].copy()
        d_row[i]    = np.inf
        order_i     = np.argsort(d_row, kind = 'stable')
        neighbor[i] = order_i[:k_neighbors].tolist()

    dont_look = [False] * N
    state     = {
        'N'          : N,
        'tour'       : tour,
        'pos'        : pos,
        'dist'       : dist,
        'neighbor'   : neighbor,
        'dont_look'  : dont_look,
        'reversed'   : False,
        'tour_length': tour_length,
        'fixed_pair' : fixed_pair,
    }

    trials = trials_param if trials_param > 0 else N
    for trial in range(1, trials + 1):
        _three_opt_pass(state)
        if state['tour_length'] < best_tour_length:
            best_tour        = list(state['tour'])
            best_tour_length = state['tour_length']
        else:
            state['tour']        = list(best_tour)
            state['pos']         = [0] * N
            for i in range(0, N):
                state['pos'][state['tour'][i]] = i
            state['tour_length'] = best_tour_length
        if N <= 5 or trial == trials:
            break
        # Reset don't-look bits before each kick so the next pass scans
        # fresh.
        state['dont_look'] = [False] * N
        _double_bridge_kick(state, rng)

    # Re-orient. The state still holds best_tour; rebuild pos.
    state['tour'] = list(best_tour)
    state['pos']  = [0] * N
    for i in range(0, N):
        state['pos'][state['tour'][i]] = i
    if fixed_pair is not None:
        # Open-path: produce a linear ordering that starts at node 0 and
        # ends at node n_path (= N - 1). The C code does:
        #   reversed = next(0) == N - 1;
        state['reversed'] = (_next_in_tour(state, 0) == N - 1)
    else:
        # Closed-cycle: arbitrary orientation, starting at node 0.
        state['reversed'] = False

    order = []
    v     = 0
    for _ in range(0, N):
        order.append(v)
        v = _NEXT(state, v)
    return order

# ---- low-level tour primitives ------------------------------------------

def _prev_in_tour(state, v):
    pos  = state['pos']
    tour = state['tour']
    N    = state['N']
    p    = pos[v]
    return tour[p - 1] if p > 0 else tour[N - 1]

def _next_in_tour(state, v):
    pos  = state['pos']
    tour = state['tour']
    N    = state['N']
    p    = pos[v]
    return tour[p + 1] if p < N - 1 else tour[0]

def _PREV(state, v):
    return _next_in_tour(state, v) if state['reversed'] else _prev_in_tour(state, v)

def _NEXT(state, v):
    return _prev_in_tour(state, v) if state['reversed'] else _next_in_tour(state, v)

def _between(state, v1, v2, v3):
    pos = state['pos']
    a   = pos[v1]
    b   = pos[v2]
    c   = pos[v3]
    if a <= c:
        return (b >= a) and (b <= c)
    return (b <= c) or (b >= a)

def _BETWEEN(state, v1, v2, v3):
    if state['reversed']:
        return _between(state, v3, v2, v1)
    return _between(state, v1, v2, v3)

def _fixed_edge(state, a, b):
    fp = state['fixed_pair']
    if fp is None:
        return False
    i, j = fp
    return (a == i and b == j) or (a == j and b == i)

def _flip(state, src, dst):
    if src == dst:
        return
    if state['reversed']:
        src, dst = dst, src
    tour = state['tour']
    pos  = state['pos']
    N    = state['N']
    i, j = pos[src], pos[dst]
    size = j - i
    if size < 0:
        size = size + N
    if size >= N // 2:
        # Reverse the complementary arc instead.
        tmp = i
        i   = j + 1 if j + 1 < N else 0
        j   = tmp - 1 if tmp - 1 >= 0 else N - 1
    while i != j:
        a, b              = tour[i], tour[j]
        tour[i], tour[j]  = b, a
        pos[a], pos[b]    = j, i
        i = i + 1 if i + 1 < N else 0
        if i != j:
            j = j - 1 if j - 1 >= 0 else N - 1

# ---- 3-opt move evaluation -----------------------------------------------

def _three_opt_pass(state):
    N         = state['N']
    dist      = state['dist']
    neighbor  = state['neighbor']
    dont_look = state['dont_look']

    improved = True
    while improved:
        improved = False
        for b in range(0, N):
            if dont_look[b]:
                continue
            dont_look[b] = True
            for xa in range(1, 3):                                           # xa loop also toggles `reversed`
                a  = _PREV(state, b)
                if _fixed_edge(state, a, b):
                    state['reversed'] = not state['reversed']
                    continue
                g0 = dist[a, b]
                for c in neighbor[b]:
                    if c == _prev_in_tour(state, b) or c == _next_in_tour(state, b):
                        continue
                    g1 = g0 - dist[b, c]
                    if g1 <= 0:
                        break                                                # neighbours sorted: no more gain
                    move_done = False
                    for xc in range(1, 3):
                        d = _PREV(state, c) if xc == 1 else _NEXT(state, c)
                        if d == a or _fixed_edge(state, c, d):
                            continue
                        g2 = g1 + dist[c, d]
                        if xc == 1:
                            gain = g2 - dist[d, a]
                            if gain > 0:
                                _flip(state, b, d)                           # 2-opt move
                                state['tour_length']  = state['tour_length'] - gain
                                dont_look[a]          = False
                                dont_look[b]          = False
                                dont_look[c]          = False
                                dont_look[d]          = False
                                improved              = True
                                move_done             = True
                                break
                        for e in neighbor[d]:
                            if e == _prev_in_tour(state, d) or e == _next_in_tour(state, d):
                                continue
                            if xc == 2 and not _BETWEEN(state, b, e, c):
                                continue
                            g3 = g2 - dist[d, e]
                            if g3 <= 0:
                                break
                            for xe in range(1, xc + 1):
                                if xc == 1:
                                    f = _NEXT(state, e) if _BETWEEN(state, b, e, c) else _PREV(state, e)
                                else:
                                    f = _PREV(state, e) if xe == 1 else _NEXT(state, e)
                                if f == a or _fixed_edge(state, e, f):
                                    continue
                                gain = g3 + dist[e, f] - dist[f, a]
                                if gain > 0:
                                    if xc == 1:
                                        _flip(state, b, d)
                                        if f == _PREV(state, e):
                                            _flip(state, e, a)
                                        else:
                                            _flip(state, a, e)
                                    elif xe == 1:
                                        _flip(state, e, c)
                                        if b == _NEXT(state, a):
                                            _flip(state, b, f)
                                        else:
                                            _flip(state, f, b)
                                    else:
                                        _flip(state, d, a)
                                        if f == _NEXT(state, e):
                                            _flip(state, f, c)
                                        else:
                                            _flip(state, c, f)
                                        if b == _NEXT(state, d):
                                            _flip(state, b, e)
                                        else:
                                            _flip(state, e, b)
                                    state['tour_length']  = state['tour_length'] - gain
                                    dont_look[a]          = False
                                    dont_look[b]          = False
                                    dont_look[c]          = False
                                    dont_look[d]          = False
                                    dont_look[e]          = False
                                    dont_look[f]          = False
                                    improved              = True
                                    move_done             = True
                                    break
                            if move_done:
                                break
                        if move_done:
                            break
                    if move_done:
                        break
                state['reversed'] = not state['reversed']

# ---- double-bridge kick (4-opt perturbation) -----------------------------

def _double_bridge_kick(state, rng):
    state['reversed'] = False
    N                 = state['N']
    pos               = state['pos']
    t                 = [-1] * 4
    for i in range(0, 4):
        t[i] = _select_t(state, i, t, rng)
        if t[i] < 0:
            return

    # Sort t so that pos[t[0]] < pos[t[1]] < pos[t[2]] < pos[t[3]].
    if pos[t[0]] > pos[t[1]]:
        t[0], t[1] = t[1], t[0]
    if pos[t[2]] > pos[t[3]]:
        t[2], t[3] = t[3], t[2]
    if pos[t[0]] > pos[t[2]]:
        t[0], t[2] = t[2], t[0]
    if pos[t[1]] > pos[t[3]]:
        t[1], t[3] = t[3], t[1]
    if pos[t[1]] > pos[t[2]]:
        t[1], t[2] = t[2], t[1]

    a = t[0]; b = _next_in_tour(state, a)
    c = t[2]; d = _next_in_tour(state, c)
    e = t[1]; f = _next_in_tour(state, e)
    g = t[3]; h = _next_in_tour(state, g)

    _flip(state, b, c)
    if f == _next_in_tour(state, e):
        _flip(state, f, h)
    else:
        _flip(state, h, f)
    if b == _next_in_tour(state, d):
        _flip(state, c, d)
    else:
        _flip(state, d, c)

    dist                  = state['dist']
    state['tour_length']  = state['tour_length'] - (
          dist[a, b] - dist[b, c]
        + dist[c, d] - dist[d, a]
        + dist[e, f] - dist[f, g]
        + dist[g, h] - dist[h, e]
    )
    for v in (a, b, c, d, e, f, g, h):
        state['dont_look'][v] = False

def _select_t(state, i, t, rng):
    N = state['N']
    r = rng.randint(0, N - 1)
    r0 = r
    while not _legal_t(state, r, i, t):
        r = r + 1 if r + 1 < N else 0
        if r == r0:
            return -1
    return r

def _legal_t(state, r, i, t):
    for j in range(0, i):
        if r == t[j]:
            return False
    return not _fixed_edge(state, r, _next_in_tour(state, r))

############################################################################

def _optimize_path(distance_matrix, path, max_neighbors, trials_param, rng):
    n_path = len(path) - 1                                                  
    if n_path < 2:
        return

    if path[0] == path[-1]:
        unique = path[:-1]                                                  
        N      = n_path                                                     
        if N < 3:
            return
        sub_ix = np.asarray(unique, dtype = np.int64)
        dist   = distance_matrix[np.ix_(sub_ix, sub_ix)].astype(np.float64, copy = True)
        np.fill_diagonal(dist, 0.0)

        order = _path_three_opt(dist, N - 1, max_neighbors, trials_param, rng, fixed_pair = None)

        if order[0] != 0:
            k     = order.index(0)
            order = order[k:] + order[:k]

        new_path = [unique[order[i]] for i in range(0, N)]
        new_path.append(new_path[0])
        for i in range(0, n_path + 1):
            path[i] = new_path[i]
        return

    sub_ix = np.asarray(path, dtype = np.int64)
    dist   = distance_matrix[np.ix_(sub_ix, sub_ix)].astype(np.float64, copy = True)
    np.fill_diagonal(dist, 0.0)
    dist[0, n_path]    = 0.0
    dist[n_path, 0]    = 0.0

    order = _path_three_opt(dist, n_path, max_neighbors, trials_param, rng, fixed_pair = (0, n_path))

    new_path = [path[order[i]] for i in range(0, n_path + 1)]
    for i in range(0, n_path + 1):
        path[i] = new_path[i]

############################################################################

def _build_path(distance_matrix, path, nb_clust, max_neighbors, trials_param, rng):
    """In-place recursive constructor on path[0..n] (n+1 elements).
    Keeps path[0] and path[n] fixed.
    """
    n = len(path) - 1
    if n <= 2:
        return
    if n <= nb_clust * nb_clust:
        _optimize_path(distance_matrix, path, max_neighbors, trials_param, rng)
        return

    # tmp_path is a working copy.
    tmp_path = list(path)

    # Position 1: the city (in tmp_path[1..n-1]) closest to path[0].
    p0      = path[0]
    dmin    = distance_matrix[tmp_path[1], p0]
    closest = 1
    for i in range(2, n):
        d = distance_matrix[tmp_path[i], p0]
        if d < dmin:
            dmin    = d
            closest = i
    tmp_path[1], tmp_path[closest] = tmp_path[closest], tmp_path[1]

    # Position 2: the city (in tmp_path[2..n-1]) closest to path[n].
    pn      = path[n]
    dmin    = distance_matrix[tmp_path[2], pn]
    closest = 2
    for i in range(3, n):
        d = distance_matrix[tmp_path[i], pn]
        if d < dmin:
            dmin    = d
            closest = i
    tmp_path[2], tmp_path[closest] = tmp_path[closest], tmp_path[2]

    # Positions 3..nb_clust: a random sample from the remaining interior.
    for i in range(3, nb_clust + 1):
        j                              = rng.randint(i, n - 1)
        tmp_path[i], tmp_path[j]       = tmp_path[j], tmp_path[i]
    tmp_path[2], tmp_path[nb_clust]    = tmp_path[nb_clust], tmp_path[2]

    # The sample path: [path[0], anchor_1, ..., anchor_{nb_clust}, path[n]].
    sample = [tmp_path[i] for i in range(0, nb_clust + 1)]
    sample.append(path[n])
    _optimize_path(distance_matrix, sample, max_neighbors, trials_param, rng)

    # Assign each interior city of path to the closest anchor.
    assignment = [0] * (n + 1)
    for i in range(1, n):
        dmin    = np.inf
        closest = 1
        pi      = path[i]
        matched = False
        for j in range(1, nb_clust + 1):
            if pi == sample[j]:
                closest = j
                matched = True
                break
            d = distance_matrix[pi, sample[j]]
            if d < dmin:
                dmin    = d
                closest = j
        assignment[i] = closest

    # Build start_clust as in the C code.
    start_clust = [0] * (nb_clust + 1)
    for i in range(1, n):
        start_clust[assignment[i]] = start_clust[assignment[i]] + 1
    for i in range(1, nb_clust + 1):
        start_clust[i] = start_clust[i] + start_clust[i - 1]

    # Place cities in tmp_path grouped by cluster, ordered along the
    # optimized sample.
    assigned = [0] * (nb_clust + 1)
    for i in range(1, n):
        k                                       = assignment[i]
        tmp_path[start_clust[k - 1] + assigned[k]] = path[i]
        assigned[k]                             = assigned[k] + 1

    for i in range(1, n):
        path[i] = tmp_path[i - 1]

    # Recurse on each cluster's sub-path. Consecutive clusters share an
    # endpoint, so the chaining is automatic.
    for i in range(0, nb_clust):
        start = start_clust[i]
        end   = start_clust[i + 1] + 1
        if end - start > 2:
            sub_path = path[start:end]
            _build_path(distance_matrix, sub_path, nb_clust, max_neighbors, trials_param, rng)
            path[start:end] = sub_path

############################################################################

def _fast_popmusic(distance_matrix, tour, R, max_neighbors, trials_param, rng):
    """`tour` is a closed Hamiltonian tour: tour[0] == tour[-1], len = n+1."""
    n = len(tour) - 1
    if R > n:
        R = n
    if R < 3:
        return

    for scan in (1, 2):
        if scan == 2:
            # Circular right shift by R // 2 (rotate the "window grid").
            shift     = R // 2
            interior  = tour[:-1]
            interior  = interior[-shift:] + interior[:-shift]
            tour[:-1] = interior
            tour[-1]  = tour[0]

        i = 0
        while i < n // R:
            sub = tour[R * i : R * i + R + 1]
            _optimize_path(distance_matrix, sub, max_neighbors, trials_param, rng)
            tour[R * i : R * i + R + 1] = sub
            i = i + 1
        if n % R != 0:
            sub = tour[n - R : n + 1]
            _optimize_path(distance_matrix, sub, max_neighbors, trials_param, rng)
            tour[n - R : n + 1] = sub

############################################################################

# Function: POPMUSIC
def popmusic(distance_matrix, sample_size = 10, max_neighbors = 5, solutions = 1, trials = 1, seed = None, verbose = True):
    distance_matrix = np.ascontiguousarray(np.array(distance_matrix, dtype = np.float64))
    if distance_matrix.ndim != 2 or distance_matrix.shape[0] != distance_matrix.shape[1]:
        raise ValueError('distance_matrix must be a square matrix')
    if np.any(distance_matrix < 0):
        raise ValueError('distance_matrix cannot contain negative distances')

    n = distance_matrix.shape[0]
    if n < 2:
        return [1, 1], 0.0
    rng = random.Random(seed)
    original_matrix = distance_matrix
    if not np.allclose(distance_matrix, distance_matrix.T, rtol = 0.0, atol = 1e-12):
        if verbose == True:
            print('Warning: distance_matrix is asymmetric. POPMUSIC is a '
                  'symmetric-TSP algorithm; optimizing on the symmetrized '
                  'matrix (D + D.T)/2 and reporting cost with the original.')
        distance_matrix = 0.5 * (distance_matrix + distance_matrix.T)

    sample_size   = max(2, min(sample_size, n))
    max_neighbors = max(1, min(max_neighbors, n - 1))
    solutions     = max(1, solutions)
    trials        = max(0, trials)

    best_tour     = None
    best_distance = float('inf')

    for s in range(0, solutions):
        # Random closed tour.
        tour    = list(range(0, n))
        rng.shuffle(tour)
        tour.append(tour[0])

        # Constructive phase.
        _build_path(distance_matrix, tour, sample_size, max_neighbors, trials, rng)
        tour[-1] = tour[0]

        # Improvement phase.
        _fast_popmusic(distance_matrix, tour, sample_size * sample_size, max_neighbors, trials, rng)
        tour[-1] = tour[0]

        d = _tour_cost(original_matrix, tour)
        if d < best_distance:
            best_distance = d
            best_tour     = list(tour)

        if verbose == True:
            print('Iteration = ', s + 1, 'Distance = ', round(best_distance, 2))

    # Convert to 1-indexed closed route (pyCombinatorial convention).
    route = [int(c) + 1 for c in best_tour]
    return route, float(best_distance)

############################################################################
