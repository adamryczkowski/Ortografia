from .question_selection import QuestionGenerator
from pathlib import Path
from .orthography_questions import OrthographyQuestion


def load_questions(file_path: Path) -> QuestionGenerator:
    with open(file_path, "r") as file:
        words = file.readlines()

    generator = QuestionGenerator()

    for word in words:
        questions = OrthographyQuestion.FromStr(word)
        for question in questions:
            generator.add_question(question)

    return generator
