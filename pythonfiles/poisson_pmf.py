import math

def poisson_pmf(k, lam):
    return math.exp(-lam) * lam**k / math.factorial(k)