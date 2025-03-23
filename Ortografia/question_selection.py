from __future__ import annotations

import heapq
import random

import numpy as np
from pydantic import BaseModel

from .beta_scoring_function import question_score
from .ifaces import I_Problem


class QuestionWithScore(BaseModel):
    question: I_Problem
    correct_count: int
    incorrect_count: int
    last_epoch: int

    def update_score(self, correct: bool, current_epoch: int):
        if correct:
            self.correct_count += 1
        else:
            self.incorrect_count += 1
        self.last_epoch = current_epoch

    def get_correctness_score(self) -> float:
        return question_score(
            positive_reviews_count=self.correct_count,
            total_reviews_count=self.correct_count + self.incorrect_count,
            CI=0.2,
        )

    def get_score_for_selection(self, current_epoch: int, add_salt: bool) -> float:
        """Returns score that is used for problem selection.
        It favors problems with lowest probability of correctness, but
        also takes into account the age of the problem, and
        disfavours problems that have been asked recently.
        """
        if add_salt:
            random_salt = random.uniform(-0.05, 0.05)
        else:
            random_salt = 0

        beta_median = question_score(
            positive_reviews_count=self.correct_count,
            total_reviews_count=self.correct_count + self.incorrect_count,
            CI=0.2 + random_salt,
        )
        decay_factor = (
            0.4  # The smaller, the bigger the delay before repeating the same question.
        )
        question_age = current_epoch - self.last_epoch

        exponential_decay = np.exp(-(question_age * decay_factor))
        return 1 * exponential_decay + beta_median * (1 - exponential_decay)


class QuestionGenerator(BaseModel):
    questions: dict[str, QuestionWithScore] = {}
    current_epoch: int = 0

    def add_question(self, question: I_Problem):
        assert question.problem_ID not in self.questions
        self.questions[question.problem_ID] = QuestionWithScore(
            question=question,
            correct_count=0,
            incorrect_count=0,
            last_epoch=self.current_epoch,
        )

    def get_question(self) -> I_Problem:
        return self.worst_question.question

    def update_question(self, question: I_Problem, correct: bool):
        q = self.questions[question.problem_ID]
        q.update_score(correct, self.current_epoch)
        self.current_epoch += 1

    def get_worst_questions(
        self, max_count: int, add_salt: bool, add_decay: bool
    ) -> list[QuestionWithScore]:
        class Q(BaseModel):
            question: QuestionWithScore
            utility: float

            def __lt__(self, other: Q):
                return self.utility < other.utility

        questions: list[Q] = []
        for q in self.questions.values():
            if add_decay:
                utility = q.get_score_for_selection(
                    self.current_epoch, add_salt=add_salt
                )
            else:
                utility = q.get_correctness_score()
            heapq.heappush(questions, Q(question=q, utility=utility))
        ans = []
        max_count = min(max_count, len(questions))
        for i in range(max_count):
            ans.append(heapq.heappop(questions).question)

        return ans

    @property
    def worst_question(self) -> QuestionWithScore:
        worst_questions = self.get_worst_questions(1, add_salt=True, add_decay=True)
        if len(worst_questions) == 0:
            print("No questions")

        return worst_questions[0]

    def get_score(self) -> float:
        questions = self.get_worst_questions(
            max_count=6, add_decay=False, add_salt=False
        )
        weights = np.ndarray(len(questions), float)
        for i in range(len(questions)):
            weights[i] = np.exp(-i * 0.5)
        weights /= weights.sum()
        scores = np.array([q.get_correctness_score() for q in questions])
        return float(np.sum(weights * scores))
