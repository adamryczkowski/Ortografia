import click
from pathlib import Path
from pydantic import TypeAdapter
from rich.console import Console
from rich.text import Text
from .analyze import UserContext
from .ifaces import I_Response, IncorrectInputError
from .orthography_questions import QuestionGeneratorForOrthography, PlaceholderType

DEFAULT_STATE_PATH = Path(__file__).parent.parent / "tests" / "quiz_state.json"
DEFAULT_DICTIONARY_FILE = Path(__file__).parent / "polish_frequent_words.txt"


@click.group()
def cli():
    pass


@click.command()
@click.argument(
    "state_file",
    type=click.Path(exists=True, path_type=Path),
    default=DEFAULT_STATE_PATH,
)
@click.argument("depth", type=int, default=20)
def analyze(state_file: Path, depth: int):
    console = Console()
    analyze = UserContext(state_file)
    console.print(analyze.rich_repr(depth))


@click.command()
@click.argument(
    "state_file",
    type=click.Path(exists=True, path_type=Path),
    default=DEFAULT_STATE_PATH,
)
@click.argument(
    "dictionary_file",
    type=click.Path(exists=True, path_type=Path),
    default=DEFAULT_DICTIONARY_FILE,
)
@click.option(
    "--placeholder-types",
    multiple=True,
    type=click.Choice(["RZ", "CH", "U"]),
    default=["RZ", "CH", "U"],
)
def load_dict(state_file: Path, dictionary_file: Path, placeholder_types: list[str]):
    console = Console()
    placeholder_types_enum = []
    for placeholder_type in placeholder_types:
        try:
            placeholder_types_enum.append(PlaceholderType[placeholder_type])
        except KeyError:
            raise ValueError(
                f"Invalid placeholder type: {placeholder_type}. "
                "Valid options are: RZ, CH, U."
            )

    greeting = Text()
    assert dictionary_file.is_file()
    with open(state_file, "r") as file:
        json = file.read()
    generator = TypeAdapter(QuestionGeneratorForOrthography).validate_json(json)
    greeting.append("Welcome! Your last session has been restored from ")
    rel_path = state_file.relative_to(Path(__file__).parent)
    greeting.append(str(rel_path), "yellow")
    greeting.append(".")
    added_count = generator.add_dictionary(dictionary_file, placeholder_types_enum)

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
    with open(DEFAULT_STATE_PATH, "w") as file:
        file.write(json)

    greeting = Text()
    greeting.append("New words have been saved into the session file")
    console.print(greeting)


@click.command()
@click.argument(
    "state_file",
    type=click.Path(exists=True, path_type=Path),
    default=DEFAULT_STATE_PATH,
)
def play(state_file: Path):
    console = Console()
    greeting = Text()
    if not state_file.is_file():
        raise Exception("State file not found. Please load a dictionary first.")
    with open(state_file, "r") as file:
        json = file.read()
    generator = TypeAdapter(QuestionGeneratorForOrthography).validate_json(json)
    greeting.append("Welcome! Your last session has been restored from ")
    try:
        rel_path = state_file.relative_to(Path(__file__).parent.parent)
    except ValueError:
        rel_path = state_file
    greeting.append(str(rel_path), "yellow")
    greeting.append(". You have given ")
    greeting.append(str(generator.current_epoch), "bold")
    greeting.append(" answers to the set of total ")
    greeting.append(str(len(generator.questions)), "bold")
    greeting.append(" questions. Your current score is: ")
    greeting.append(f"{generator.get_score():.1%}", "bold")
    greeting.append(".")

    console.print(greeting)
    delta_score = 0
    response = None

    while True:
        with console.screen(hide_cursor=False):
            response_text = Text()
            if response is not None:
                if response.is_correct:
                    response_text.append("Correct", "bold green")
                else:
                    response_text.append("Incorrect", "bold red")
            else:
                response_text.append("Current score: ")

            response_text.append(f"{generator.get_score():.1%}", "bold")
            if delta_score < -0.0005:
                response_text.append(" (")
                response_text.append(f"{delta_score:.2%}", "red")
                response_text.append(" change).")
            elif delta_score > 0.0005:
                response_text.append(" (")
                response_text.append(f"{delta_score:.2%}", "green")
                response_text.append(" change).")

            console.print(response_text)

            json = generator.model_dump_json()
            with open(state_file, "w") as file:
                file.write(json)

            question = generator.get_question()

            response = None
            while True:
                console.print(question.user_prompt_string())
                answer = input("Your answer: ").strip()
                try:
                    response = question.parse_user_response(answer)
                except IncorrectInputError as e:
                    console.print(str(e))
                    continue
                except Exception:
                    raise
                break

            assert isinstance(response, I_Response)

            previous_score = generator.get_score()
            generator.update_question(question, response.is_correct)
            current_score = generator.get_score()
            delta_score = current_score - previous_score


cli.add_command(analyze)
cli.add_command(load_dict)
cli.add_command(play)

if __name__ == "__main__":
    cli()
