from __future__ import annotations

import heapq
import random

import numpy as np
from pydantic import BaseModel

from .beta_scoring_function import question_score
from .ifaces import I_Problem
from rich.text import Text


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

    def rich_repr(self) -> Text:
        ans = Text.assemble(
            self.question.short_user_prompt_string(),
            Text(" correct - incorrect: "),
            Text(str(self.correct_count), "bold"),
            Text(" - "),
            Text(str(self.incorrect_count), "bold"),
            Text(". Score: "),
            Text(f"{self.get_correctness_score():.2%}", "bold red"),
        )
        return ans

    def __repr__(self) -> str:
        word = self.question.short_user_prompt_string()
        word = repr(word)
        ans = f"{word} correct - incorrect: {self.correct_count} - {self.incorrect_count}. Score: {self.get_correctness_score():.2%}"
        return ans


class QuestionGenerator(BaseModel):
    questions: dict[str, QuestionWithScore] = {}
    current_epoch: int = 0

    def add_question(
        self, question: I_Problem, correct_count: int = 0, incorrect_count: int = 0
    ):
        assert question.problem_ID not in self.questions
        self.questions[question.problem_ID] = QuestionWithScore(
            question=question,
            correct_count=correct_count,
            incorrect_count=incorrect_count,
            last_epoch=0,
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
            max_count=self.score_depth, add_decay=False, add_salt=False
        )
        weights = self.get_weights()
        scores = np.array([q.get_correctness_score() for q in questions])
        return float(np.sum(weights * scores))

    @property
    def answer_count(self) -> tuple[int, int]:
        """Returns the total number of answers given: positive and negative."""
        total_correct = sum(q.correct_count for q in self.questions.values())
        total_incorrect = sum(q.incorrect_count for q in self.questions.values())
        return total_correct, total_incorrect

    @property
    def score_depth(self) -> int:
        """Returns the depth of the score calculation, which is the number of questions considered."""
        return 20

    def get_weights(self) -> list[float]:
        weights = np.ndarray(self.score_depth, float)
        for i in range(self.score_depth):
            weights[i] = np.exp(-i * 0.05)
        weights /= weights.sum()
        return list(weights)

    def clone(self) -> QuestionGenerator:
        """Returns a clone of the current generator."""
        return QuestionGenerator(
            questions={k: v.copy() for k, v in self.questions.items()},
            current_epoch=self.current_epoch,
        )
