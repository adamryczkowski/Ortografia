from pathlib import Path
import heapq
import re
import random
from pydantic import BaseModel, TypeAdapter


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


def main():
    file_path = Path(__file__).parent / "quiz_input.txt"
    state_path = Path(__file__).parent / "quiz_state.json"
    if state_path.is_file():
        with open(state_path, "r") as file:
            json = file.read()
        generator = TypeAdapter(QuestionGenerator).validate_json(json)
    else:
        generator = load_questions(file_path)
    pattern = re.compile(r"^.*(ch|(?<!c)h).*$", re.IGNORECASE)
    pattern_partial = re.compile(r"(ch|(?<!c)h)", re.IGNORECASE)
    while True:
        json = generator.model_dump_json()
        with open(state_path, "w") as file:
            file.write(json)

        question = generator.get_question()
        if question is None:
            break
        match = re.match(pattern, question.word)
        correct_answer = match.group(1).lower()
        censored_question = re.sub(pattern_partial, "[ch|h]", question.word)
        while True:
            print(f"Spell the word correctly: {censored_question}")
            answer = input("Your answer: ").strip()
            if answer.lower() != "h" and answer.lower() != "ch":
                if answer.lower() == question.word.lower():
                    user_is_correct = True
                else:
                    if correct_answer.lower() == "ch":
                        incorrect_answer = "h"
                    else:
                        incorrect_answer = "ch"
                    if answer.lower() == re.sub(
                        pattern_partial, incorrect_answer, question.word
                    ):
                        user_is_correct = False
                    else:
                        print("What? I don't understand. Type 'ch' or 'h'")
                        continue
            else:
                user_is_correct = answer.lower() == correct_answer
            generator.update_question(question, user_is_correct)
            if user_is_correct:
                print(f"Correct. Score: {generator.total_score}")
            else:
                print(f"Incorrect. True answer: {correct_answer}")
            break


if __name__ == "__main__":
    main()
