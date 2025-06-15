from pathlib import Path

from rich.console import Console

from Ortografia import UserContext
import time


def test_analyze():
    console = Console(color_system="truecolor")
    state_path = Path(__file__).parent / "quiz_state.json"
    analyze = UserContext(state_path)

    while True:
        console.print(analyze.get_report(20))
        time.sleep(1)


if __name__ == "__main__":
    test_analyze()
