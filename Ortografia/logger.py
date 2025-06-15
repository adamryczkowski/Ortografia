import csv
import datetime
from pathlib import Path
from typing import Optional


class ResponseLogger:
    """A logger class for recording user responses to orthography questions."""

    def __init__(self, log_file: Optional[Path] = None):
        """Initialize the logger with a path to the log file.

        Args:
            log_file: Path to the log file. If None, a default path will be used.
        """
        if log_file is None:
            log_file = Path.home() / "ortografia_responses.csv"

        self.log_file = log_file
        self._ensure_log_file_exists()

    def _ensure_log_file_exists(self) -> None:
        """Ensure the log file exists and has proper headers."""
        if not self.log_file.exists():
            with open(self.log_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(
                    ["datetime", "epoch", "question_id", "given_answer", "is_correct"]
                )

    def log_response(
        self, epoch: int, question_id: str, given_answer: str, is_correct: bool
    ) -> None:
        """Log a user response to a question.

        Args:
            epoch: The current epoch of the quiz.
            question_id: The ID of the question being answered.
            given_answer: The answer provided by the user.
            is_correct: Whether the answer was correct.
        """
        timestamp = datetime.datetime.now().isoformat()

        with open(self.log_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, epoch, question_id, given_answer, is_correct])
