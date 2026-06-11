import poisson_pmf
import dixon_coles_tau_FIXED

#def dixon_coles_pmf(x, y, lam1, lam2, rho):
def dixon_coles_pmf(x, y, lam1, lam2, rho,fase):
    base = poisson_pmf.poisson_pmf(x, lam1) * poisson_pmf.poisson_pmf(y, lam2)
    return base * dixon_coles_tau_FIXED.dixon_coles_tau(x, y, lam1, lam2, rho,fase)
    #return base * dixon_coles_tau.dixon_coles_tau(x, y, lam1, lam2, rho)