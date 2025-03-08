import heapq
import random
from pathlib import Path

from pydantic import BaseModel

from .beta_scoring_function import question_score


class Question(BaseModel):
    word: str
    correct_answer_count: int = 0
    incorrect_answer_count: int = 0
    last_asked: int = 0

    def update_score(self, correct: bool):
        if correct:
            self.correct_answer_count += 1
        else:
            self.incorrect_answer_count += 1

    def get_score(self, current_epoch: int, add_salt: bool = True) -> float:
        if add_salt:
            random_salt = random.uniform(-0.05, 0.05)
        else:
            random_salt = 0

        beta_median = question_score(
            positive_reviews_count=self.correct_answer_count,
            total_reviews_count=self.correct_answer_count + self.incorrect_answer_count,
            CI=0.2 + random_salt,
        )

        # exponential_decay = np.exp(-(current_epoch - self.last_asked) / beta_median)
        # exponential_decay acts as a component that artificially increases score of the recently-answered question, to prevent the program from asking it again.

        # beta_median is a better version of an expected probability of giving the next answer correct.

        # decay_component = current_epoch - self.last_asked + 1
        return beta_median


class QuestionGenerator(BaseModel):
    questions: dict[str, Question] = {}
    epoch: int = 0
    total_score: int = 0

    def add_question(self, question: Question):
        self.questions[question.word] = question

    def get_question(self) -> Question:
        return self.worst_question

    def update_question(self, question: Question, correct: bool):
        question.update_score(correct)
        self.add_question(question)
        if correct:
            self.total_score += 1
        else:
            self.total_score -= 3

    @property
    def worst_question(self) -> Question:
        class Q(BaseModel):
            question: Question
            utility: float

            def __lt__(self, other: Question):
                return self.utility < other.utility

        self.epoch += 1
        questions: list[Q] = []
        for q in self.questions.values():
            heapq.heappush(
                questions, Q(question=q, utility=q.get_score(self.epoch, False))
            )

        question: Question = questions[0].question
        return question

    def get_score(self, add_salt: bool = True) -> float:
        return self.worst_question.get_score(0, add_salt)


def load_questions(file_path: Path) -> QuestionGenerator:
    with open(file_path, "r") as file:
        words = file.readlines()
    questions = [Question(word=word.strip()) for word in words]
    generator = QuestionGenerator()
    for question in questions:
        generator.add_question(question)
    return generator
