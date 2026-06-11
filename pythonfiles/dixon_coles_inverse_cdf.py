import dixon_coles_cdf

def dixon_coles_inverse_cdf(p, lam1, lam2, rho, max_goals=5):
    """
    Encuentra el menor par (k1, k2) tal que
    P(X <= k1, Y <= k2) >= p
    """

    if not (0 < p < 1):
        raise ValueError("p debe estar entre 0 y 1")

    for k1 in range(max_goals + 1):
        for k2 in range(max_goals + 1):
            if dixon_coles_cdf.dixon_coles_cdf(k1, k2, lam1, lam2, rho) >= p:
                return k1, k2

    raise RuntimeError("No se alcanzó la probabilidad con max_goals dado")