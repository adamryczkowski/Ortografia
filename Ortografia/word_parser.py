from .question_selection import QuestionGenerator
from pathlib import Path
from .orthography_questions import (
    OrthographyQuestion,
    QuestionGeneratorForOrthography,
    PlaceholderType,
)


def load_questions(
    file_path: Path, placeholder_types: list[PlaceholderType] | None = None
) -> QuestionGenerator:
    with open(file_path, "r") as file:
        words = file.readlines()

    generator = QuestionGeneratorForOrthography()

    for word in words:
        questions = OrthographyQuestion.FromStr(
            word.strip(), placeholder_types=placeholder_types
        )
        for question in questions:
            while question.problem_ID in generator.questions:
                if question.id_suffix == "":
                    question.id_suffix = "1"
                else:
                    val = int(question.id_suffix)
                    val += 1
                    question.id_suffix = f"{val}"
            generator.add_question(question)

    return generator
