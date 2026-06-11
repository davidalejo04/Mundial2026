import random
def sample_score_from_cdf(cdf):
    u = random.random()
    for threshold, score in cdf:
        if u <= threshold:
            return score