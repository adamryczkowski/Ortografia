from __future__ import annotations
import random

from pydantic import BaseModel

from .beta_scoring_function import question_score
import numpy as np


class Question(BaseModel):
    word: str
    correct_answer_count: int = 0
    incorrect_answer_count: int = 0
    last_asked: int = 0

    def update_last_epoch(self, epoch: int) -> None:
        self.last_asked = epoch

    def update_score(self, correct: bool):
        if correct:
            self.correct_answer_count += 1
        else:
            self.incorrect_answer_count += 1

    def get_score(
        self, current_epoch: int, add_salt: bool = True, add_decay: bool = True
    ) -> float:
        decay_factor = 1.0
        if add_salt:
            random_salt = random.uniform(-0.05, 0.05)
        else:
            random_salt = 0

        beta_median = question_score(
            positive_reviews_count=self.correct_answer_count,
            total_reviews_count=self.correct_answer_count + self.incorrect_answer_count,
            CI=0.2 + random_salt,
        )
        question_age = self.last_asked - current_epoch

        if add_decay:
            exponential_decay = np.exp(-(question_age * decay_factor))
        else:
            exponential_decay = 0.0

        return exponential_decay + beta_median * (1 - exponential_decay)
