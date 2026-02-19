############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: pyCombinatorial - RSS (Randomized Spectral Seriation)
 
# GitHub Repository: <https://github.com/Valdecy> 

############################################################################

# Required Libraries
import numpy as np

from numba import njit
from scipy.sparse import coo_matrix, diags
from scipy.sparse.linalg import eigsh, ArpackNoConvergence

############################################################################

# Numba Functions
@njit(fastmath = True, cache = True)
def tour_length(tour, D):
    n = len(tour)
    L = 0.0
    for i in range(n - 1):
        L = L + D[tour[i], tour[i + 1]]
    L = L +  D[tour[n - 1], tour[0]]
    return L

@njit(fastmath = True, cache = True)
def _reverse_segment_inplace(tour, pos, p1, p2, n):
    if p1 <= p2:
        while p1 < p2:
            tmp           = tour[p1]
            tour[p1]      = tour[p2]
            tour[p2]      = tmp
            pos[tour[p1]] = p1
            pos[tour[p2]] = p2
            p1            = p1 + 1
            p2            = p2 - 1
    else:
        seg_len = (p2 - p1 + n) % n + 1
        seg     = np.empty(seg_len, dtype=np.int32)
        for s in range(seg_len):
            seg[s] = tour[(p1 + s) % n]
        for s in range(seg_len):
            ni            = (p1 + s) % n
            tour[ni]      = seg[seg_len - 1 - s]
            pos[tour[ni]] = ni

@njit(fastmath = True, cache = True)
def two_opt_candidates_restart(tour, D, candidates, max_passes):
    n   = len(tour)
    pos = np.empty(n, dtype = np.int32)
    for i in range(n):
        pos[tour[i]] = i
    passes       = 0
    improved_any = True
    while improved_any and passes < max_passes:
        passes       = passes + 1
        improved_any = False
        for i in range(0, n):
            a             = tour[i]
            b             = tour[(i + 1) % n]
            dab           = D[a, b]
            improved_here = False
            for which_end in range(2):
                x = a if which_end == 0 else b
                for ci in range(candidates.shape[1]):
                    c = candidates[x, ci]
                    if D[x, c] >= dab:
                        break
                    j = pos[c]
                    d = tour[(j + 1) % n]
                    if d == a or d == b:
                        continue
                    gain = dab + D[c, d] - D[a, c] - D[b, d]
                    if gain > 1e-12:
                        p1            = (i + 1) % n
                        p2            = j
                        _reverse_segment_inplace(tour, pos, p1, p2, n)
                        improved_any  = True
                        improved_here = True
                        break
                if improved_here:
                    break
    return tour

############################################################################

# Function: KNN
def knn_indices_fast(D, k):
    n           = D.shape[0]
    k           = int(min(k, n - 1))
    pool        = min(n, k + max(16, k // 2))
    part        = np.argpartition(D, kth = pool - 1, axis = 1)[:, :pool]
    rows        = np.arange(n)[:, None]
    dvals       = D[rows, part]
    order       = np.argsort(dvals, axis = 1)
    part_sorted = part[rows, order]
    nbrs        = np.empty((n, k), dtype = np.int32)
    for i in range(0, n):
        out = []
        for v in part_sorted[i]:
            v = int(v)
            if v != i:
                out.append(v)
            if len(out) == k:
                break
        if len(out) < k:
            pool2 = pool
            while len(out) < k:
                if pool2 >= n:
                    break
                pool2 = min(n, max(pool2 + 32, int(pool2 * 1.5), k + 16))
                part2 = np.argpartition(D[i], kth = pool2 - 1)[:pool2]
                part2 = part2[np.argsort(D[i, part2])]
                out   = []
                for v in part2:
                    v = int(v)
                    if v != i:
                        out.append(v)
                    if len(out) == k:
                        break
        nbrs[i, :] = np.array(out[:k], dtype = np.int32)
    return nbrs

# Function: Affinity
def build_affinity_sparse(D, k, sigma_mode, sigma_fixed):
    n    = D.shape[0]
    nbrs = knn_indices_fast(D.astype(float), k)
    if sigma_mode == 'adaptive':
        sig = D[np.arange(n), nbrs[:, -1]].astype(float) + 1e-12
    else:
        sig = np.full(n, sigma_fixed, dtype = float)
    rows, cols, vals = [], [], []
    for i in range(n):
        si = sig[i]
        for j in nbrs[i]:
            sj = sig[j]
            dij = float(D[i, j])
            if sigma_mode == 'adaptive':
                w = np.exp(-(dij * dij) / (si * sj + 1e-12))
            else:
                w = np.exp(-(dij * dij) / (2.0 * sigma_fixed * sigma_fixed + 1e-12))
            rows.append(i); cols.append(j); vals.append(w)
    W = coo_matrix((vals, (rows, cols)), shape = (n, n)).tocsr()
    W = (W + W.T).tocsr()      
    W = W.tolil()              
    W.setdiag(0.0)
    W = W.tocsr()
    W.eliminate_zeros()
    return W

# Function: W
def laplacian_from_W(W):
    d = np.array(W.sum(axis = 1)).reshape(-1)
    return (diags(d) - W).tocsr()

# Function: SE
def spectral_embedding(L, num_vecs = 3, tol = 1e-6, maxiter = 5000):
    n = L.shape[0]
    if n <= 2:
        return np.zeros((n, 1), dtype = float)
    num_vecs = int(max(1, min(num_vecs, n - 1)))
    k_req    = min(num_vecs + 3, n - 1)
    k_req    = max(k_req, 2)
    try:
        vals, vecs = eigsh(L, k = k_req, which = 'SM', tol = tol, maxiter = maxiter)
    except ArpackNoConvergence as e:
        if e.eigenvectors is not None and e.eigenvalues is not None:
            vals, vecs = e.eigenvalues, e.eigenvectors
        else:
            k_req2     = max(2, min(k_req - 1, n - 1))
            vals, vecs = eigsh(L, k = k_req2, which = 'SM', tol = tol, maxiter = maxiter)
    idx  = np.argsort(vals)
    vals = vals[idx]
    vecs = vecs[:, idx]
    eps  = 1e-10
    j    = 0
    while j < len(vals) and vals[j] < eps:
        j = j + 1
    if j >= len(vals):
        j = 1
    end = min(j + num_vecs, vecs.shape[1])
    if end <= j:
        end = min(j + 1, vecs.shape[1])
    return vecs[:, j:end].copy()

############################################################################

# RSS
def randomized_spectral_seriation(D, k = 12, iterations = 800, sigma_noise = 0.006, sigma_mode = 'adaptive', sigma_fixed = 250.0, two_opt_passes = 30, num_vecs = 3, cand_k = 35, scale_noise_by_std = True, noise_cap_frac = 0.10, rnd = 7, verbose = True):
    D   = np.asarray(D, dtype = np.float64)
    n   = D.shape[0]
    rng = np.random.default_rng(rnd)
    if n < 3:
        tour = list(range(1, n + 1))
        if n > 0:
            tour.append(tour[0])
        return tour, 0.0
    k         = int(max(1, min(k, n - 1)))
    cand_k    = int(max(1, min(cand_k, n - 1)))
    W         = build_affinity_sparse(D, k, sigma_mode, sigma_fixed)
    L         = laplacian_from_W(W)
    embedding = spectral_embedding(L, num_vecs = num_vecs, tol = 1e-6, maxiter = 5000)
    m         = embedding.shape[1]
    if m <= 0:
        embedding = np.zeros((n, 1), dtype = float)
        m = 1
    candidates = knn_indices_fast(D, cand_k)
    best_L     = float("inf")
    best_tour  = None
    for it in range(0, iterations):
        coeffs    = rng.normal(0.0, 1.0, size = m)
        if m > 0:
            coeffs[0] = 3.0 * coeffs[0]
        coeffs = coeffs/(np.linalg.norm(coeffs) + 1e-12)
        x_proj = embedding @ coeffs
        if scale_noise_by_std:
            s     = float(np.std(x_proj) + 1e-12)
            eff   = sigma_noise * s
            cap   = noise_cap_frac * float((np.max(x_proj) - np.min(x_proj)) + 1e-12)
            eff   = min(eff, cap)
            noise = rng.normal(0.0, eff, size = n)
        else:
            noise = rng.normal(0.0, sigma_noise, size = n)
        x_noisy   = x_proj + noise
        candidate = np.argsort(x_noisy).astype(np.int32)
        if rng.random() < 0.5:
            candidate = candidate[::-1].copy()
        shift     = int(rng.integers(0, n))
        candidate = np.roll(candidate, shift).astype(np.int32)
        candidate = two_opt_candidates_restart(candidate, D, candidates, max(two_opt_passes, 2))
        Lc        = tour_length(candidate, D)
        if Lc < best_L:
            best_L    = Lc
            best_tour = candidate.copy()
        if verbose:
            print("Iteration =", it, "; Distance =", best_L)
    best_out = (best_tour + 1).tolist()
    best_out.append(best_out[0])
    return best_out, float(best_L)

############################################################################