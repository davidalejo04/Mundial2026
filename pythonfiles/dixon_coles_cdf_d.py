import dixon_coles_pmf
import adjust_parameters
#def build_dixon_coles_cdf_d(lam1, lam2, rho, max_goals=6):
def build_dixon_coles_cdf_d(lam1, lam2, rho,fase,mode, max_goals=5):
    outcomes = []
    total_prob = 0.0

    ## nueva funcionalidad: adjust parameters:

    lam1,lam2=adjust_parameters.adjust_parameters(lam1,lam2,fase,mode)

    ## aca termina la nueva funcionalidad

    # generar todos los marcadores
    for x in range(max_goals + 1):
        for y in range(max_goals + 1):
            p = dixon_coles_pmf.dixon_coles_pmf(x, y, lam1, lam2, rho,fase)
            #p = dixon_coles_pmf.dixon_coles_pmf(x, y, lam1, lam2, rho)
            outcomes.append(((x, y), p))
            total_prob += p

    # normalizar (por truncamiento)
    outcomes = [((x, y), p / total_prob) for (x, y), p in outcomes]

    # CDF acumulada
    cdf = []
    cumulative = 0.0
    for (x, y), p in outcomes:
        cumulative += p
        cdf.append((cumulative, (x, y)))

    return cdf