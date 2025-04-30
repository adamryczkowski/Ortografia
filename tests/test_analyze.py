from pathlib import Path

from rich.console import Console

from Ortografia import UserContext


def test_analyze():
    console = Console()
    state_path = Path(__file__).parent / "quiz_state_saved2.json"
    analyze = UserContext(state_path)

    console.print(analyze.rich_repr(20))


if __name__ == "__main__":
    test_analyze()
