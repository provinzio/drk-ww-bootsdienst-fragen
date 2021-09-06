import enum
import re
import random
import collections

from xml.sax.saxutils import escape
from tkinter import Tk


class Question:
    def __init__(self, question: str) -> None:
        self.question = question
        # Erste Antwort muss korrekt sein.
        self.answers: list[str] = []

    def __repr__(self) -> str:
        return f"\n\nFRAGE :: {self.question}: \n" + "\n".join(self.answers)

    def addAnswer(self, answer: str) -> None:
        self.answers.append(answer)


class Topic:
    def __init__(self) -> None:
        self.questions: list[Question] = []

    def addQuestion(self, question: Question) -> None:
        self.questions.append(question)


questions: list[Question] = []
topics: dict[str, list[Question]] = collections.defaultdict(list)

with open("data/20190127_DRK-WW_BD_Fragenkatalog.pdf.txt", "r", encoding="utf8") as f:
    question = None
    current_topic = None
    answer_buffer: list[str] = []

    for line in f:
        line = line.removeprefix("\ufeff").replace("\t", " ").replace("  ", " ").strip()

        if m := re.match(r"^\# \d+ (.*)$", line):
            # if "Regional" in line:
            #     break
            # Abschnitt.
            current_topic = m.group(1)
            continue

        if m := re.match(r"^\d+ \(\d+\) (.*)", line):

            if question is not None:
                if answer_buffer:
                    # Neue Frage, vorherige Antwort speichern.
                    question.addAnswer(" :: ".join(answer_buffer))
                    # Antwort-Buffer leeren.
                    answer_buffer = []
                # vorherige Frage speichern.
                assert (
                    len(question.answers) == 4
                ), f"Es sind nicht genau vier Antwortmöglichkeiten: {question.question}"
                questions.append(question)
                topics[current_topic].append(question)
                # print(question)

            # Neue Frage
            question = Question(m.group(1))
            # question = Question(line)
            continue

        assert isinstance(
            question, Question
        ), f"Es muss bereits eine Frage geben, {question.__class__.__name__}"

        if line == "BILD FEHLT":
            # question.question += line
            continue

        if m := re.match(r"□ [ABCD] (.*)", line):
            if answer_buffer:
                # Neue Antwort, vorherige Antwort speichern.
                question.addAnswer(" :: ".join(answer_buffer))
                # Antwort-Buffer leeren.
                answer_buffer = []

            answer_buffer.append(m.group(1))
        else:
            assert answer_buffer, f"Es gibt noch keine Antwort zum Puffern. {line}"
            answer_buffer.append(line)


with open("sailtrainer/drkwwfragen.xml", "w", encoding="utf8") as f:
    f.writelines(
        [
            "<?xml version='1.0' standalone='yes'?>\n",
            "<questionaire xmlns='http://sportboot.mobi/'>\n",
        ]
    )

    unique_id = 3000
    question_id = 1
    for _, (topic, questions) in enumerate(topics.items(), 1):
        f.writelines([f"<topic id='{unique_id}' name='{escape(topic)}'>\n"])
        unique_id += 1

        for _, question in enumerate(questions):
            assert len(question.answers) == 4
            f.writelines(
                [
                    f"  <question id='{unique_id}' reference='{question_id}'>\n",
                    f"    <text>{escape(question.question)}</text>\n",
                    f"    <correct>{escape(question.answers[0])}</correct>\n",
                    f"    <incorrect>{escape(question.answers[1])}</incorrect>\n",
                    f"    <incorrect>{escape(question.answers[2])}</incorrect>\n",
                    f"    <incorrect>{escape(question.answers[3])}</incorrect>\n",
                    "  </question>\n",
                ]
            )
            unique_id += 1
            question_id += 1

        f.writelines(["</topic>\n"])
    f.writelines(["</questionaire>\n"])


# XX = "\n".join(
#     "\t".join(
#         (
#             str(i),
#             q.question,
#             q.answers[0],
#             "1",
#             q.answers[1],
#             "",
#             q.answers[2],
#             "",
#             q.answers[3],
#         )
#     )
#     for i, q in enumerate(questions)
# )

# with open("output.txt", "w", encoding="utf8") as f:
#     f.write(XX)


# def xshuffle(l: list) -> list:
#     x = l.copy()
#     random.shuffle(x)
#     return x


# for i in range(5):
#     random.shuffle(questions)
#     with open(f"random-{i}.txt", "w", encoding="utf8") as f:
#         f.write(
#             "\n\n".join(
#                 f"{q.question}\n"
#                 + "\n".join(f"{i}) {a}" for i, a in enumerate(xshuffle(q.answers), 1))
#                 for q in questions
#             )
#         )
