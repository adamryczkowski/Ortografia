from __future__ import annotations

import random
from builtins import enumerate
from typing import override

from .ifaces import I_Response, I_Problem, IncorrectInputError
from .question_selection import QuestionGenerator, QuestionWithScore
from enum import Enum
from pydantic import BaseModel
from rich.text import Text
import re


class MaskType(Enum):
    PLACEHOLDER = 0
    CORRECT = 1
    INCORRECT = 2
    AMBIGUOUS = 3


class MaskStyle(Enum):
    NORMAL = 0
    BOLD = 1
    BOLD_BLUE = 2

    def mask_string(self) -> str:
        if self == MaskStyle.NORMAL:
            return ""
        elif self == MaskStyle.BOLD:
            return "bold"
        elif self == MaskStyle.BOLD_BLUE:
            return "bold on blue"
        else:
            raise ValueError(f"Unknown mask style {self}")


class PlaceholderType(Enum):
    RZ = 1
    CH = 2
    U = 3


def build_regexp_from_placeholders(placeholders: list[PlaceholderType]) -> str:
    ans = []
    for placeholder in placeholders:
        if placeholder == PlaceholderType.RZ:
            ans.append(r"rz|ż")
        elif placeholder == PlaceholderType.CH:
            ans.append(r"ch|(?<!c)h")
        elif placeholder == PlaceholderType.U:
            ans.append("[uó]")
        else:
            raise ValueError(f"Unknown placeholder type {placeholder}")

    regex = r"|".join(ans)
    # regex = f"^(.*({regex}))+.*$"
    return regex


class InputPlaceholder(BaseModel):
    placeholder_type: PlaceholderType
    value: bool = False  # True means the letter from the placeholder label, False means the alternative.
    content: str  # The correct string to be put into the placeholder

    @property
    def ambiguous_placeholder(self) -> str:
        if self.placeholder_type == PlaceholderType.RZ:
            return "rz/ż"
        elif self.placeholder_type == PlaceholderType.CH:
            return "ch/h"
        elif self.placeholder_type == PlaceholderType.U:
            return "u/ó"
        else:
            raise ValueError(f"Unknown placeholder type {self.placeholder_type}")

    def render_ambiguous_placeholder(self, emphasize: bool) -> Text:
        ans = Text()
        style = "bold on blue" if emphasize else "gray"
        ans.append(self.ambiguous_placeholder, style=style)
        return ans

    def render_correct_placeholder(self, emphasize: bool) -> Text:
        ans = Text()
        style = "bold" if emphasize else ""
        ans.append(self.content, style=style)
        return ans

    def _a_letter(self, incorrect: bool) -> str:
        if self.placeholder_type == PlaceholderType.RZ:
            return "rz" if self.value != incorrect else "ż"
        elif self.placeholder_type == PlaceholderType.CH:
            return "ch" if self.value != incorrect else "h"
        elif self.placeholder_type == PlaceholderType.U:
            return "u" if self.value != incorrect else "ó"
        else:
            raise ValueError(f"Unknown placeholder type {self.placeholder_type}")

    @property
    def correct_letter(self) -> str:
        return self._a_letter(incorrect=False)

    @property
    def incorrect_letter(self) -> str:
        return self._a_letter(incorrect=True)


class OrthographyQuestion(I_Problem):
    word: str  # String that contains placeholder character ("_") for the missing letter(s).
    placeholders: list[
        tuple[int, InputPlaceholder]
    ]  # Sorted by int, the index of the placeholder in the word.
    target_placeholder_idx: (
        int  # Index of the placeholder that the user should fill in.
    )
    id_suffix: str = ""  # In case of ambiguity

    @staticmethod
    def FromStr(
        word: str, placeholder_types: list[PlaceholderType] | None = None
    ) -> list[OrthographyQuestion]:
        if placeholder_types is None:
            placeholder_types = [
                PlaceholderType.RZ,
                PlaceholderType.CH,
                PlaceholderType.U,
            ]
        null_char = "_"
        null_pattern = re.compile(null_char)
        # Check if the word contains no null placeholders
        if null_pattern.search(word) is not None:
            raise ValueError(f"Word cannot contain '{null_char}'")

        regexp = build_regexp_from_placeholders(placeholder_types)
        pattern = re.compile(regexp, re.IGNORECASE)

        matches = pattern.finditer(word)
        #         matches = re.findall(pattern, word)
        ans = []

        # Replace the placeholders with the null character
        placeholded_word = re.sub(pattern, null_char, word)

        placeholded_matches = null_pattern.finditer(placeholded_word)
        placeholders = []

        for i, (match, placeholded_match) in enumerate(
            zip(matches, placeholded_matches)
        ):
            start, end = match.span()
            content = word[start:end]
            start, end = placeholded_match.span()

            if content == "rz" or content == "ż":
                placeholders.append(
                    (
                        start,
                        InputPlaceholder(
                            placeholder_type=PlaceholderType.RZ,
                            value=content.lower() == "rz",
                            content=content,
                        ),
                    )
                )
            elif content == "ch" or content == "h":
                placeholders.append(
                    (
                        start,
                        InputPlaceholder(
                            placeholder_type=PlaceholderType.CH,
                            value=content.lower() == "ch",
                            content=content,
                        ),
                    )
                )
            elif content == "u" or content == "ó":
                placeholders.append(
                    (
                        start,
                        InputPlaceholder(
                            placeholder_type=PlaceholderType.U,
                            value=content.lower() == "u",
                            content=content,
                        ),
                    )
                )
            else:
                raise ValueError(f"Unknown placeholder {content}")
        for i in range(len(placeholders)):
            question = OrthographyQuestion(
                word=placeholded_word,
                placeholders=placeholders,
                target_placeholder_idx=i,
            )
            # print(question.get_incorrect_word_str())
            ans.append(question)
        return ans

    def __init__(
        self,
        word: str,
        placeholders: list[tuple[int, InputPlaceholder]],
        target_placeholder_idx: int,
        id_suffix: str = "",
    ) -> None:
        super().__init__(
            word=word,  # pyright:ignore[reportCallIssue]
            placeholders=placeholders,  # pyright:ignore[reportCallIssue]
            target_placeholder_idx=target_placeholder_idx,  # pyright:ignore[reportCallIssue]
            id_suffix=id_suffix,  # pyright: ignore [reportCallIssue]
        )

    @property
    def target_placeholder(self) -> InputPlaceholder:
        return self.placeholders[self.target_placeholder_idx][1]

    @property
    @override
    def problem_ID(self) -> str:
        ans = ""
        placeholder_idx = 0
        last_str_pos = 0
        while placeholder_idx < len(self.placeholders):
            placeholder = self.placeholders[placeholder_idx]
            ans += self.word[
                last_str_pos : placeholder[0]
            ]  # Beginning of the word, excluding the first placeholder
            ans += (
                placeholder[1].correct_letter
                if self.target_placeholder_idx != placeholder_idx
                else "_"
            )

            last_str_pos = placeholder[0] + 1
            placeholder_idx += 1

        ans += self.word[last_str_pos:]  # The rest of the word
        return ans + self.id_suffix

    @override
    def user_prompt_string(self) -> Text:
        return Text.assemble(
            "Spell the blue part correctly: ", self.get_ambiguous_word2()
        )

    @override
    def short_user_prompt_string(self) -> Text:
        return self.get_word_masked_on_target()

    @override
    def parse_user_response(self, answer: str) -> I_Response:
        answer = answer.strip().lower()
        if answer == self.target_placeholder.correct_letter:
            return OrthographyResponse(user_response_correct=True, question=self)
        elif answer == self.target_placeholder.incorrect_letter:
            return OrthographyResponse(user_response_correct=False, question=self)

        if answer == self.get_correct_word_str():
            return OrthographyResponse(user_response_correct=True, question=self)
        if answer == self.get_incorrect_word_str():
            return OrthographyResponse(user_response_correct=False, question=self)

        raise IncorrectInputError(f"Unknown answer {answer}")

    def get_correct_word(self) -> Text:
        ans = Text()
        placeholder_idx = 0
        last_str_pos = 0
        while placeholder_idx < len(self.placeholders):
            placeholder = self.placeholders[placeholder_idx]
            ans.append(
                self.word[last_str_pos : placeholder[0]]
            )  # Beginning of the word, excluding the first placeholder
            ans.append(
                placeholder[1].render_correct_placeholder(
                    self.target_placeholder_idx == placeholder_idx
                )
            )

            last_str_pos = placeholder[0] + 1
            placeholder_idx += 1

        ans.append(self.word[last_str_pos:])  # The rest of the word
        return ans

    def get_correct_word_str(self) -> str:
        ans = ""
        placeholder_idx = 0
        last_str_pos = 0
        while placeholder_idx < len(self.placeholders):
            placeholder = self.placeholders[placeholder_idx]
            ans += self.word[
                last_str_pos : placeholder[0]
            ]  # Beginning of the word, excluding the first placeholder
            ans += placeholder[1].content

            last_str_pos = placeholder[0] + 1
            placeholder_idx += 1

        ans += self.word[last_str_pos:]  # The rest of the word
        return ans

    def get_incorrect_word_str(self) -> str:
        ans = ""
        placeholder_idx = 0
        last_str_pos = 0
        while placeholder_idx < len(self.placeholders):
            placeholder = self.placeholders[placeholder_idx]
            ans += self.word[
                last_str_pos : placeholder[0]
            ]  # Beginning of the word, excluding the first placeholder
            if self.target_placeholder_idx != placeholder_idx:
                ans += placeholder[1].incorrect_letter
            else:
                ans += placeholder[1].correct_letter

            last_str_pos = placeholder[0] + 1
            placeholder_idx += 1

        ans += self.word[last_str_pos:]  # The rest of the word
        return ans

    # def get_ambiguous_word(self, mask_only_one: bool = False) -> Text:
    #     ans = Text()
    #     placeholder_idx = 0
    #     last_str_pos = 0
    #     while placeholder_idx < len(self.placeholders):
    #         placeholder = self.placeholders[placeholder_idx]
    #         ans.append(
    #             self.word[last_str_pos: placeholder[0]]
    #         )  # Beginning of the word, excluding the first placeholder
    #         if self.target_placeholder_idx != placeholder_idx:
    #             if mask_only_one:
    #                 ans = Text.assemble(
    #                     ans, placeholder[1].render_correct_placeholder(False)
    #                 )
    #             else:
    #                 ans.append(placeholder[1].render_ambiguous_placeholder(False))
    #         else:
    #             ans.append(placeholder[1].render_ambiguous_placeholder(True))
    #
    #         last_str_pos = placeholder[0] + 1
    #         placeholder_idx += 1
    #
    #     ans.append(self.word[last_str_pos:])
    #     return ans

    def render_word(
        self,
        mask_style_of_target: MaskStyle,
        mask_type_of_target: MaskType,
        mask_style_of_other: MaskStyle,
        mask_type_of_other: MaskType,
    ) -> Text:
        ans = Text()
        placeholder_idx = 0
        last_str_pos = 0
        while placeholder_idx < len(self.placeholders):
            placeholder = self.placeholders[placeholder_idx]
            ans.append(
                self.word[last_str_pos : placeholder[0]]
            )  # Beginning of the word, excluding the first placeholder
            if self.target_placeholder_idx != placeholder_idx:
                style = mask_style_of_other.mask_string()
                if mask_type_of_other == MaskType.PLACEHOLDER:
                    ans.append("_", style)
                elif mask_type_of_other == MaskType.CORRECT:
                    ans.append(placeholder[1].correct_letter, style)
                elif mask_type_of_other == MaskType.INCORRECT:
                    ans.append(placeholder[1].incorrect_letter, style)
                elif mask_type_of_other == MaskType.AMBIGUOUS:
                    ans.append(placeholder[1].ambiguous_placeholder, style)
                else:
                    raise ValueError(f"Unknown mask type {mask_type_of_other}")
            else:
                style = mask_style_of_target.mask_string()
                if mask_type_of_target == MaskType.PLACEHOLDER:
                    ans.append("_", style)
                elif mask_type_of_target == MaskType.CORRECT:
                    ans.append(placeholder[1].correct_letter, style)
                elif mask_type_of_target == MaskType.INCORRECT:
                    ans.append(placeholder[1].incorrect_letter, style)
                elif mask_type_of_target == MaskType.AMBIGUOUS:
                    ans.append(placeholder[1].ambiguous_placeholder, style)
                else:
                    raise ValueError(f"Unknown mask type {mask_type_of_target}")

            last_str_pos = placeholder[0] + 1
            placeholder_idx += 1

        ans.append(self.word[last_str_pos:])
        return ans

    def get_ambiguous_word(self) -> Text:
        return self.render_word(
            mask_type_of_target=MaskType.PLACEHOLDER,
            mask_type_of_other=MaskType.PLACEHOLDER,
            mask_style_of_target=MaskStyle.BOLD_BLUE,
            mask_style_of_other=MaskStyle.BOLD,
        )

    def get_ambiguous_word2(self) -> Text:
        b = bool(random.getrandbits(1))
        ans = Text.assemble(
            self.get_word_unmasked_on_target(b),
            Text(
                " / ",
            ),
            self.get_word_unmasked_on_target(not b),
        )
        return ans

    def get_word_masked_on_target(self) -> Text:
        return self.render_word(
            mask_type_of_target=MaskType.PLACEHOLDER,
            mask_type_of_other=MaskType.CORRECT,
            mask_style_of_target=MaskStyle.BOLD_BLUE,
            mask_style_of_other=MaskStyle.NORMAL,
        )

    def get_word_unmasked_on_target(self, correct: bool) -> Text:
        if correct:
            type = MaskType.CORRECT
        else:
            type = MaskType.INCORRECT
        return self.render_word(
            mask_type_of_target=type,
            mask_type_of_other=MaskType.PLACEHOLDER,
            mask_style_of_target=MaskStyle.BOLD_BLUE,
            mask_style_of_other=MaskStyle.NORMAL,
        )


class OrthographyResponse(I_Response):
    user_response_correct: bool
    question: OrthographyQuestion

    @property
    @override
    def is_correct(self) -> bool:
        return self.user_response_correct


class _QuestionWithScore_Orthography(QuestionWithScore):
    question: OrthographyQuestion  # pyright: ignore [reportIncompatibleVariableOverride]


class QuestionGeneratorForOrthography(QuestionGenerator):
    questions: dict[str, _QuestionWithScore_Orthography] = {}  # pyright: ignore [reportIncompatibleVariableOverride]
