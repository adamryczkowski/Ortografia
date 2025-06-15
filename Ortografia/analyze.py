# This module contains a human-readable summary of the user's progress.
from pathlib import Path

import numpy as np
import pandas as pd
from pydantic import TypeAdapter
from rich.table import Table

from .orthography_questions import QuestionGeneratorForOrthography
from .question_selection import QuestionGenerator, QuestionWithScore


class UserContext:
    _gen: QuestionGenerator
    _last_state: pd.DataFrame | None  # Columns: word, ok, bad, score, score_weight
    _last_report: Table | None
    _state_path: Path | None = None

    def __init__(self, state_json: Path):
        self._state_path = state_json
        with open(state_json, "r") as file:
            json = file.read()
        self._gen = TypeAdapter(QuestionGeneratorForOrthography).validate_json(json)
        self._last_state = None
        self._last_report = None

    def get_state(self) -> pd.DataFrame:
        """Loads the current state into the Pandas DataFrame."""
        with open(str(self._state_path), "r") as file:
            json = file.read()
        self._gen = TypeAdapter(QuestionGeneratorForOrthography).validate_json(json)
        total_len = len(self._gen.questions)
        worst_questions = self.worst_n_questions(total_len)
        weights = self._gen.get_weights()

        df = pd.DataFrame(
            {
                "word": [q.question.problem_ID for q in worst_questions],
                "ok": [q.correct_count for q in worst_questions],
                "bad": [q.incorrect_count for q in worst_questions],
                "score": [q.get_correctness_score() for q in worst_questions],
                "score_weight": [
                    weights[i] if i < len(weights) else 0 for i in range(total_len)
                ],
            }
        )

        df.sort_values(by="score_weight", ascending=False, inplace=True)
        return df

    def worst_n_questions(self, n: int) -> list[QuestionWithScore]:
        return self._gen.get_worst_questions(n, add_salt=False, add_decay=False)

    def get_report(self, depth: int) -> Table:
        """Generates a report of the user's progress."""
        current_state = self.get_state()
        if self._last_state is not None and not are_scores_different(
            depth, self._last_state, current_state
        ):
            assert self._last_report is not None
            return self._last_report

        score = self._gen.get_score()

        total_ok, total_bad = self._gen.answer_count

        table = Table(title=f"Score: {score:.2%}, OK: {total_ok}, Bad: {total_bad}")
        table.add_column("Change", justify="left")
        table.add_column("Word", justify="left")
        table.add_column("OK", justify="left", style="dark_green")
        table.add_column("Bad", justify="left", style="dark_red")
        table.add_column("Score", justify="right")
        table.add_column("ΔFailure", justify="right", style="dark_red")
        table.add_column("ΔSuccess", justify="right", style="dark_green")

        for pos, q in enumerate(self.worst_n_questions(depth)):
            alt_gen_pos = self._gen.clone()
            alt_gen_pos.update_question(q.question, True)  # Assume all are correct
            alt_gen_neg = self._gen.clone()
            alt_gen_neg.update_question(q.question, False)  # Assume all are correct
            alg_pos = alt_gen_pos.get_score() - score
            alg_neg = score - alt_gen_neg.get_score()

            if self._last_state is not None:
                # last_pos = self._last_state.loc[self._last_state['word'] == q.question.short_user_prompt_string()]
                last_pos = self._last_state.index[
                    self._last_state["word"] == q.question.problem_ID
                ].tolist()
                last_pos = last_pos[0] if last_pos else None

            else:
                last_pos = None

            if last_pos is None:
                change = "[green]New"
                ok_field = str(q.correct_count)
                bad_field = str(q.incorrect_count)
                score_field = f"{q.get_correctness_score():.2%}"

            else:
                assert self._last_state is not None
                if last_pos > pos:
                    change = "[red bold]↑"
                elif last_pos < pos:
                    change = "[green bold]↓"
                else:
                    change = "[gray]="

                last_ok = self._last_state.loc[last_pos]["ok"]
                if last_ok > q.correct_count:
                    ok_field = f"{last_ok}[red]–{last_ok - q.correct_count}"
                elif last_ok < q.correct_count:
                    ok_field = f"{last_ok}[green]+{q.correct_count - last_ok}"
                else:
                    ok_field = f"{last_ok}  "
                last_bad = self._last_state.loc[last_pos]["bad"]
                if last_bad > q.incorrect_count:
                    bad_field = f"{last_bad}[green]+{last_bad - q.incorrect_count}"
                elif last_bad < q.incorrect_count:
                    bad_field = f"{last_bad}[red]–{q.incorrect_count - last_bad}"
                else:
                    bad_field = f"{last_bad}  "
                last_score = self._last_state.loc[last_pos]["score"]
                if last_score > q.get_correctness_score():
                    score_field = f"{last_score:.2%}[red]–{(last_score - q.get_correctness_score()):.2%}"
                elif last_score < q.get_correctness_score():
                    score_field = f"{last_score:.2%}[green]+{(q.get_correctness_score() - last_score):.2%}"
                else:
                    score_field = f"{last_score:.2%}      "

            table.add_row(
                change,
                q.question.short_user_prompt_string(),
                ok_field,
                bad_field,
                score_field,
                f"–{alg_neg:.2%}",
                f"+{alg_pos:.2%}",
            )

        self._last_state = current_state
        self._last_report = table
        return table


def are_scores_different(
    depth: int, score1: pd.DataFrame, score2: pd.DataFrame
) -> bool:
    """Compares two DataFrames to check if they are different."""
    if score1.shape != score2.shape:
        return True
    dic_score1 = {}
    for i, (_, rec) in enumerate(score1.iterrows()):
        if i > depth:
            break
        word1 = rec["word"]
        dic_score1[word1] = rec["score"]

    dic_score2 = {}
    for i, (_, rec) in enumerate(score2.iterrows()):
        if i > depth:
            break
        word2 = rec["word"]
        dic_score2[word2] = rec["score"]

    if len(dic_score1) != len(dic_score2):
        return True

    for word in dic_score1:
        if word not in dic_score2:
            return True
        if not np.isclose(dic_score1[word], dic_score2[word]):
            return True

    return False
