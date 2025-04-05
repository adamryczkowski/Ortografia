from .question_selection import QuestionGenerator
from pathlib import Path
from .orthography_questions import (
    QuestionGeneratorForOrthography,
    PlaceholderType,
)


def load_questions(
    file_path: Path, placeholder_types: list[PlaceholderType] | None = None
) -> QuestionGenerator:
    generator = QuestionGeneratorForOrthography()
    generator.add_dictionary(file_path, placeholder_types=placeholder_types)

    return generator
