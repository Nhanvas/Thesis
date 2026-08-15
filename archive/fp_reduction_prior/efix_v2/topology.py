"""
topology.py
===========
Graph spectral anomaly scoring for EEG connectivity matrices.

Four features per window:
  1. Spectral radius   λ_max = max|eigenvalue(A)|
     - Measures dominant connectivity strength; changes when hub nodes shift
  2. Graph energy      E = Σ|eigenvalue(A)|
     - Total spectral weight; sensitive to global connectivity reorganization
  3. Fiedler value     λ_2(L_norm) = 2nd smallest eigenvalue of normalized Laplacian
     - Algebraic connectivity; drops when graph becomes less connected
  4. Degree entropy    H = -Σ p_i log(p_i), p_i = degree_i / Σdegree
     - Network hub structure; changes when connectivity becomes more concentrated

Anomaly score = L2 norm of z-normalized feature vector (per-subject interictal stats).
This is direction-agnostic: captures both increase and decrease in any feature.
"""

import numpy as np


def compute_window_topology(A: np.ndarray) -> np.ndarray:
    """
    Compute 4 topology features for one adjacency matrix.

    Parameters
    ----------
    A : np.ndarray, shape [18, 18]
        Weighted symmetric adjacency matrix (topk20 sparse).

    Returns
    -------
    np.ndarray, shape [4] — [spectral_radius, graph_energy, fiedler, degree_entropy]
    """
    # Eigenvalues of symmetric A — fast via eigvalsh
    eigvals = np.linalg.eigvalsh(A)           # [18], real, sorted

    # 1. Spectral radius
    spectral_radius = np.max(np.abs(eigvals))

    # 2. Graph energy
    graph_energy = np.sum(np.abs(eigvals))

    # 3. Fiedler value (normalized Laplacian)
    degree = A.sum(axis=1)                    # [18]
    eps = 1e-10
    d_inv_sqrt = np.where(degree > eps,
                          1.0 / np.sqrt(degree + eps), 0.0)
    D_inv_sqrt = np.diag(d_inv_sqrt)
    L = np.diag(degree) - A
    L_norm = D_inv_sqrt @ L @ D_inv_sqrt
    lap_eigs = np.sort(np.linalg.eigvalsh(L_norm))
    fiedler = float(lap_eigs[1]) if len(lap_eigs) > 1 else 0.0

    # 4. Degree entropy
    deg_sum = degree.sum()
    if deg_sum > eps:
        p = degree / deg_sum
        degree_entropy = float(-np.sum(p * np.log(p + eps)))
    else:
        degree_entropy = 0.0

    return np.array([spectral_radius, graph_energy, fiedler, degree_entropy],
                    dtype=np.float32)


def compute_topology_matrix(adj_path: str) -> np.ndarray:
    """
    Compute topology features for all windows in an adj file.

    Parameters
    ----------
    adj_path : str
        Path to *_adjs_topk20.npy, shape [N, 18, 18].

    Returns
    -------
    np.ndarray, shape [N, 4]
    """
    adjs = np.load(adj_path)        # [N, 18, 18]
    N = len(adjs)
    features = np.zeros((N, 4), dtype=np.float32)
    for i in range(N):
        features[i] = compute_window_topology(adjs[i])
    return features


def topology_anomaly_score(
    features_inter: np.ndarray,
    features_test: np.ndarray
) -> np.ndarray:
    """
    Compute topology anomaly score using L2 norm of z-normalized features.

    Steps:
      1. Compute per-feature median and MAD from interictal features
      2. Z-normalize both interictal and test features
      3. Score = L2 norm over 4 features per window (direction-agnostic)

    Parameters
    ----------
    features_inter : [N_inter, 4] — interictal topology features
    features_test  : [N_test,  4] — test window topology features

    Returns
    -------
    scores_inter : [N_inter] — topology anomaly scores for interictal
    scores_test  : [N_test]  — topology anomaly scores for test windows
    stats        : dict with medians, MADs for each feature
    """
    median = np.median(features_inter, axis=0)   # [4]
    mad    = np.median(np.abs(features_inter - median), axis=0) + 1e-8  # [4]

    z_inter = (features_inter - median) / mad     # [N_inter, 4]
    z_test  = (features_test  - median) / mad     # [N_test,  4]

    # L2 norm: sqrt(mean(z^2)) — equivalent to RMS of z-scores
    scores_inter = np.sqrt(np.mean(z_inter ** 2, axis=1))   # [N_inter]
    scores_test  = np.sqrt(np.mean(z_test  ** 2, axis=1))   # [N_test]

    stats = {
        "feature_names": ["spectral_radius", "graph_energy", "fiedler", "degree_entropy"],
        "median":        median.tolist(),
        "mad":           mad.tolist(),
    }
    return scores_inter, scores_test, stats