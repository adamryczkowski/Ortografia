from pathlib import Path

from pydantic import TypeAdapter
from rich.console import Console
from rich.text import Text

from Ortografia import load_questions, QuestionGenerator, IncorrectInputError


def main2():
    console = Console()
    file_path = Path(__file__).parent / "quiz_input.txt"
    state_path = Path(__file__).parent / "quiz_state.json"
    greeting = Text()
    if state_path.is_file():
        with open(state_path, "r") as file:
            json = file.read()
        generator = TypeAdapter(QuestionGenerator).validate_json(json)
        greeting.append("Welcome! You will be asked to spell a set of ")
        greeting.append(str(len(generator.questions)), "bold")
        greeting.append(" questions.")
    else:
        generator = load_questions(file_path)
        greeting.append("Welcome! Your last session has been restored. You have given ")
        greeting.append(str(generator.current_epoch), "bold")
        greeting.append(" answers to the set of total ")
        greeting.append(str(len(generator.questions)), "bold")
        greeting.append(" questions. Your current score is: ")
        greeting.append(f"{generator.get_score():.1%}", "bold")
        greeting.append(".")

    console.print(greeting)

    while True:
        json = generator.model_dump_json()
        with open(state_path, "w") as file:
            file.write(json)

        question = generator.get_question()

        while True:
            console.print(question.user_prompt_string())
            answer = input("Your answer: ").strip()
            previous_score = generator.get_score()
            try:
                response = question.parse_user_response(answer)
            except IncorrectInputError as e:
                console.print(str(e))
                continue
            break

        current_score = generator.get_score()
        delta_score = current_score - previous_score
        generator.update_question(question, response.is_correct)
        response_text = Text()
        if response.is_correct:
            response_text.append("Correct", "bold green")
        else:
            response_text.append("Incorrect", "bold red")

        response_text.append(f". {generator.get_score():.1%}", "bold")
        if delta_score < 0.001:
            response_text.append(" (")
            response_text.append(f"{previous_score:.1%}", "red")
            response_text.append(" change)")
        elif delta_score > 0.001:
            response_text.append(" (")
            response_text.append(f"{previous_score:.1%}", "green")
            response_text.append(" change)")

        response_text.append(".")


#
# def main():
#     file_path = Path(__file__).parent / "quiz_input.txt"
#     state_path = Path(__file__).parent / "quiz_state.json"
#     if state_path.is_file():
#         with open(state_path, "r") as file:
#             json = file.read()
#         generator = TypeAdapter(QuestionGenerator).validate_json(json)
#     else:
#         generator = load_questions(file_path)
#
#     pattern = re.compile(r"^.*(ch|(?<!c)h).*$", re.IGNORECASE)
#     pattern_partial = re.compile(r"(ch|(?<!c)h)", re.IGNORECASE)
#     while True:
#         json = generator.model_dump_json()
#         with open(state_path, "w") as file:
#             file.write(json)
#
#         question = generator.get_question()
#         if question is None:
#             break
#         # match = re.match(pattern, question.word)
#         # correct_answer = match.group(1).lower()
#         # censored_question = re.sub(pattern_partial, "[ch|h]", question.word)
#         while True:
#             print(f"Spell the word correctly: {censored_question}")
#             answer = input("Your answer: ").strip()
#             if answer.lower() != "h" and answer.lower() != "ch":
#                 if answer.lower() == question.word.lower():
#                     user_is_correct = True
#                 else:
#                     if correct_answer.lower() == "ch":
#                         incorrect_answer = "h"
#                     else:
#                         incorrect_answer = "ch"
#                     if answer.lower() == re.sub(
#                             pattern_partial, incorrect_answer, question.word
#                     ):
#                         user_is_correct = False
#                     else:
#                         print("What? I don't understand. Type 'ch' or 'h'")
#                         continue
#             else:
#                 user_is_correct = answer.lower() == correct_answer
#             generator.update_question(question, user_is_correct)
#             if user_is_correct:
#                 print(f"Correct. Score: {generator.get_score(False):.1%}")
#             else:
#                 print(
#                     f"Incorrect. True answer: {correct_answer}. Score: {generator.get_score(False):.1f%}"
#                 )
#             break


if __name__ == "__main__":
    main2()
