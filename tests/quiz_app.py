import re
from pathlib import Path

from pydantic import TypeAdapter

from Ortografia import QuestionGenerator, load_questions


def main():
    file_path = Path(__file__).parent / "quiz_input.txt"
    state_path = Path(__file__).parent / "quiz_state.json"
    if state_path.is_file():
        with open(state_path, "r") as file:
            json = file.read()
        generator = TypeAdapter(QuestionGenerator).validate_json(json)
    else:
        generator = load_questions(file_path)
    pattern = re.compile(r"^.*(ch|(?<!c)h).*$", re.IGNORECASE)
    pattern_partial = re.compile(r"(ch|(?<!c)h)", re.IGNORECASE)
    while True:
        json = generator.model_dump_json()
        with open(state_path, "w") as file:
            file.write(json)

        question = generator.get_question()
        if question is None:
            break
        match = re.match(pattern, question.word)
        correct_answer = match.group(1).lower()
        censored_question = re.sub(pattern_partial, "[ch|h]", question.word)
        while True:
            print(f"Spell the word correctly: {censored_question}")
            answer = input("Your answer: ").strip()
            if answer.lower() != "h" and answer.lower() != "ch":
                if answer.lower() == question.word.lower():
                    user_is_correct = True
                else:
                    if correct_answer.lower() == "ch":
                        incorrect_answer = "h"
                    else:
                        incorrect_answer = "ch"
                    if answer.lower() == re.sub(
                        pattern_partial, incorrect_answer, question.word
                    ):
                        user_is_correct = False
                    else:
                        print("What? I don't understand. Type 'ch' or 'h'")
                        continue
            else:
                user_is_correct = answer.lower() == correct_answer
            generator.update_question(question, user_is_correct)
            if user_is_correct:
                print(f"Correct. Score: {generator.total_score}")
            else:
                print(f"Incorrect. True answer: {correct_answer}")
            break


if __name__ == "__main__":
    main()
