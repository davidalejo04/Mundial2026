import dixon_coles_pmf

def dixon_coles_cdf(k1, k2, lam1, lam2, rho):
    total = 0.0
    for x in range(k1 + 1):
        for y in range(k2 + 1):
            total += dixon_coles_pmf.dixon_coles_pmf(x, y, lam1, lam2, rho)
    return total