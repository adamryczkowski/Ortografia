from pathlib import Path

from pydantic import TypeAdapter
from rich.console import Console
from rich.text import Text

from Ortografia import (
    QuestionGeneratorForOrthography,
    PlaceholderType,
)


def add_dictionary(dictionary_file: Path) -> None:
    console = Console()
    state_path = Path(__file__).parent / "quiz_state_saved.json"
    greeting = Text()
    assert dictionary_file.is_file()
    with open(state_path, "r") as file:
        json = file.read()
    generator = TypeAdapter(QuestionGeneratorForOrthography).validate_json(json)
    greeting.append("Welcome! Your last session has been restored from ")
    rel_path = state_path.relative_to(Path(__file__).parent)
    greeting.append(str(rel_path), "yellow")
    greeting.append(".")
    added_count = generator.add_dictionary(
        dictionary_file, [PlaceholderType.RZ, PlaceholderType.CH, PlaceholderType.U]
    )

    greeting.append(" ")
    greeting.append(str(added_count), "red bold")
    greeting.append(" new words added to the dictionary.\n")

    greeting.append("You have given ")
    greeting.append(str(generator.current_epoch), "bold")
    greeting.append(" answers to the set of total ")
    greeting.append(str(len(generator.questions)), "bold")
    greeting.append(" questions. Your current score is: ")
    greeting.append(f"{generator.get_score():.1%}", "bold")
    greeting.append(".")
    console.print(greeting)

    json = generator.model_dump_json()
    state_path = Path(__file__).parent / "quiz_state_saved2.json"
    with open(state_path, "w") as file:
        file.write(json)

    greeting = Text()
    greeting.append("New words has been saved into the session file")
    console.print(greeting)


if __name__ == "__main__":
    add_dictionary(Path(__file__).parent / "polish_frequent_words.txt")
