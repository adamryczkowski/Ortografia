from scipy.special import betaincinv


def question_score(
    positive_reviews_count: int, total_reviews_count: int, CI: float = 0.5
) -> float:
    median = betaincinv(
        1 + positive_reviews_count, 1 - positive_reviews_count + total_reviews_count, CI
    )
    return median
