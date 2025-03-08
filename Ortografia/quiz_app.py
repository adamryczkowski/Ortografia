import heapq
import random
from pathlib import Path

from pydantic import BaseModel


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

    def get_score(self, current_epoch: int) -> float:
        random_salt = random.uniform(
            -1 / (current_epoch - self.last_asked + 1),
            1 / (current_epoch - self.last_asked + 1),
        )

        # beta_median

        # decay_component = current_epoch - self.last_asked + 1
        return (self.correct_answer_count - self.incorrect_answer_count) + random_salt


class QuestionGenerator(BaseModel):
    questions: list[Question] = []
    epoch: int = 0
    total_score: int = 0

    def add_question(self, question: Question):
        self.questions.append(question)

    def get_question(self) -> Question:
        class Q(BaseModel):
            question: Question
            utility: float

            def __lt__(self, other: Question):
                return self.utility < other.utility

        self.epoch += 1
        questions: list[Q] = []
        for q in self.questions:
            heapq.heappush(questions, Q(question=q, utility=q.get_score(self.epoch)))

        question: Question = questions[0].question
        question.last_asked = self.epoch
        return question

    def update_question(self, question: Question, correct: bool):
        question.update_score(correct)
        self.add_question(question)
        if correct:
            self.total_score += 1
        else:
            self.total_score -= 3


def load_questions(file_path: Path) -> QuestionGenerator:
    with open(file_path, "r") as file:
        words = file.readlines()
    questions = [Question(word=word.strip()) for word in words]
    generator = QuestionGenerator()
    for question in questions:
        generator.add_question(question)
    return generator
