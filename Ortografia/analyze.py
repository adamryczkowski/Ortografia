# This module contains a human-readable summary of the user's progress.

from .question_selection import QuestionGenerator, QuestionWithScore
from pydantic import TypeAdapter
from .orthography_questions import QuestionGeneratorForOrthography
from pathlib import Path
from rich.text import Text


class UserContext:
    state: QuestionGenerator

    def __init__(self, state_json: Path):
        with open(state_json, "r") as file:
            json = file.read()
        self.state = TypeAdapter(QuestionGeneratorForOrthography).validate_json(json)

    def worst_n_questions(self, n: int) -> list[QuestionWithScore]:
        return self.state.get_worst_questions(n, add_salt=False, add_decay=False)

    def rich_repr(self, depth: int) -> Text:
        worst_questions = self.worst_n_questions(depth)

        weights = self.state.get_weights(len(worst_questions))

        ans = Text.assemble(
            Text(f"Record of {len(worst_questions)} worst questions:"),
            Text("\n"),
            *[
                Text.assemble(
                    q.rich_repr(),
                    Text(", score_weight: "),
                    Text(f"{weights[i]:.0%}", "blue"),
                    Text("\n"),
                )
                for i, q in enumerate(worst_questions)
            ],
        )
        return ans
