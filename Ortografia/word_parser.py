from .question_selection import QuestionGenerator
from pathlib import Path
from .orthography_questions import OrthographyQuestion, QuestionGeneratorForOrthography


def load_questions(file_path: Path) -> QuestionGenerator:
    with open(file_path, "r") as file:
        words = file.readlines()

    generator = QuestionGeneratorForOrthography()

    for word in words:
        questions = OrthographyQuestion.FromStr(word.strip())
        for question in questions:
            generator.add_question(question)

    return generator
