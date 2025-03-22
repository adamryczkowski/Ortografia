from __future__ import annotations
from abc import ABC, abstractmethod
from pydantic import BaseModel
from rich.text import Text


class IncorrectInputError(Exception):
    pass


class I_Problem(BaseModel, ABC):
    @property
    @abstractmethod
    def problem_ID(self) -> str:
        """String that uniqually identifies the problem"""

    @abstractmethod
    def user_prompt_string(self) -> Text: ...

    @abstractmethod
    def parse_user_response(self, answer: str) -> I_Response: ...


class I_Response(ABC, BaseModel):
    @property
    @abstractmethod
    def is_correct(self) -> bool: ...
