import collections
import itertools
import os
import pickle
import random
import re
from typing import Optional
from xml.sax.saxutils import escape

import matplotlib.image as mpimg
import matplotlib.pyplot as plt

CREATE_RANDOMIZED_TXT = False
SAVE_QUESTIONS_FOR_SAILTRAINER = False

START_QUIZ = True
IGNORE_REGIONAL = True
QUIZ_STATISIC_WIDTH = 50
QUIZ_SAVE_FILE = "quiz_save.cfg"


assert not (
    SAVE_QUESTIONS_FOR_SAILTRAINER and IGNORE_REGIONAL
), "SAVE_QUESTIONS_FOR_SAILTRAINER und IGNORE_REGIONAL können nicht gleichzeitig gesetzt sein."


class Question:
    """Eine Question besteht aus einer Frage und einer Liste von Antworten.

    Die erste Antwort in der Liste ist die korrekte Antwort.
    Grundsätzlich hat eine Frage vier Antworten.
    """

    def __init__(self, question: str, identifier: int, no: int) -> None:
        """Initialisiere eine Frage.

        Args:
            question (str): Fragestellung.
            identifier (int): Eindeutige Nummer der Frage.
            no (int): Nummer der Frage innerhalb eines Topics.
        """
        self.question = question
        self.identifier = identifier
        self.no = no
        self.has_picture = False
        # Erste Antwort muss korrekt sein.
        self.answers: list[str] = []

        # Variablen, die für das Quiz verwendet werden.
        self.correct_guess = 0
        self.false_guess = 0

    @property
    def weight(self) -> float:
        weight = max(1, self.correct_guess - self.false_guess)
        if weight > 5:
            return 0
        return 5 / weight

    @property
    def level(self) -> int:
        return self.correct_guess - self.false_guess

    @property
    def picture_path(self) -> str:
        assert self.has_picture
        return f"sailtrainer/q{self.identifier}.png"

    def __repr__(self) -> str:
        return f"\n\nFRAGE :: {self.question}: \n" + "\n".join(self.answers)

    def addAnswer(self, answer: str) -> None:
        self.answers.append(answer)


class Topic:
    """Ein Topic besteht aus einer Liste von Fragen."""

    def __init__(self) -> None:
        self.questions: list[Question] = []

    def addQuestion(self, question: Question) -> None:
        self.questions.append(question)


def xshuffle(items: list) -> list:
    """Gebe eine Kopie einer Liste zurück, die zufällig sortiert ist.

    Args:
        items (list): Liste.

    Returns:
        list: Kopie einer zufällig sortierten Liste.
    """
    shuffled_items = items.copy()
    random.shuffle(shuffled_items)
    return shuffled_items


# Lese die Topics und Fragen ein.
questions: list[Question] = []
topics: dict[str, list[Question]] = collections.defaultdict(list)

with open("data/20190127_DRK-WW_BD_Fragenkatalog.pdf.txt", "r", encoding="utf8") as f:
    question = None
    current_topic = None
    answer_buffer: list[str] = []

    for line in f:
        # Bereinige die Zeile
        line = line.removeprefix("\ufeff").replace("\t", " ").replace("  ", " ").strip()

        # Prüfe, ob die Zeile ein neues Topic einleitet.
        if m := re.match(r"^\# \d+ (.*)$", line):
            current_topic = m.group(1)
            continue

        # Prüfe, ob die Zeile eine neue Frage einleitet.
        if m := re.match(r"(^\d+) \((\d+)\) (.*)", line):
            if question is not None:
                # Es gab vorher schon eine Frage.
                # Speichere die letzte Frage in der Fragenliste.
                if answer_buffer:
                    # Neue Frage, vorheriger Antwort speichern.
                    question.addAnswer(" :: ".join(answer_buffer))
                    # Antwort-Buffer leeren.
                    answer_buffer = []
                # Vorherige Frage speichern.
                assert (
                    len(question.answers) == 4
                ), f"Es sind nicht genau vier Antwortmöglichkeiten: {question.question}"
                questions.append(question)
                topics[current_topic].append(question)

            # Lege die neue Frage an.
            identifier, no, question_text = m.groups()
            question = Question(question_text, int(identifier), int(no))
            continue

        assert isinstance(
            question, Question
        ), f"Es muss bereits eine Frage geben, {question.__class__.__name__}"

        if line == "BILD FEHLT":
            question.has_picture = True
            continue

        # Prüfe, ob die Frage eine neue Antwort beinhaltet.
        if m := re.match(r"□ [ABCD] (.*)", line):
            if answer_buffer:
                # Neue Antwort, vorherige Antwort speichern.
                question.addAnswer(" :: ".join(answer_buffer))
                # Antwort-Buffer leeren.
                answer_buffer = []

            (answer_text,) = m.groups()
            answer_buffer.append(answer_text)
            continue

        # Die vorherigen Fälle sind nicht eingetreten.
        # Die Zeile gehört zur vorherigen Antwort.
        # Nehme sie mit im Buffer auf.
        assert answer_buffer, f"Es gibt noch keine Antwort zum Puffern. {line}"
        answer_buffer.append(line)

if IGNORE_REGIONAL:
    topics = {key: value for key, value in topics.items() if "Regional" not in key}

if SAVE_QUESTIONS_FOR_SAILTRAINER:
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

if CREATE_RANDOMIZED_TXT:
    for i in range(5):
        random.shuffle(questions)
        with open(f"random-{i}.txt", "w", encoding="utf8") as f:
            f.write(
                "\n\n".join(
                    f"{q.question}\n"
                    + "\n".join(
                        f"{i}) {a}" for i, a in enumerate(xshuffle(q.answers), 1)
                    )
                    for q in questions
                )
            )


def ask_question(question: Question) -> Optional[bool]:
    print()
    print()
    print(question.question)

    # Schreibe die Antworten in zufälliger Reihenfolge.
    answer_idxs = [i for i in range(len(question.answers))]
    shuffled_answer_idxs = xshuffle(answer_idxs)
    # Die erste Antwort ist immer richtig.
    correct_answer_idx = shuffled_answer_idxs.index(0)

    for answer_idx, shuffled_answer_idx in zip(answer_idxs, shuffled_answer_idxs):
        print(f"{answer_idx+1}. {question.answers[shuffled_answer_idx]}")

    first_try_correct = True

    while True:
        try:
            input_ = input("Antwort (beenden mit q): ")
        except KeyboardInterrupt:
            return None

        if input_ in ("q", "quit"):
            return None

        try:
            input_idx = int(input_) - 1
        except ValueError:
            # Erneute Eingabe!
            continue

        if input_idx >= 0 and input_idx < len(question.answers):
            # Die Eingabe ist zulässig.

            # Werte die Antwort aus.
            if input_idx == correct_answer_idx:
                return first_try_correct
            # Wenn es beim ersten Mal nicht geklappt hat, muss der Nutzer es erneut versuchen.
            # Die Antwort zählt dann aber nicht mehr als richig.
            first_try_correct = False
            print(f"Die richtige Antwort wäre {correct_answer_idx + 1} gewesen.")
        else:
            # Ansonsten erfolgt eine erneute Eingabe.
            continue


def print_quiz_statistic(questions: list[Question]) -> None:
    print()
    print()

    n = len(questions)
    question_levels = [q.level for q in questions]
    statistic = collections.Counter(question_levels)

    for level in sorted(statistic):
        count = statistic[level]
        width = QUIZ_STATISIC_WIDTH * count // n
        spaces = QUIZ_STATISIC_WIDTH - width
        bar = width * "#" + spaces * " "
        print(f"Level {level:3}: {count:4} / {n} |{bar}|")


if START_QUIZ:
    # root = tk.Tk()

    all_questions = list(itertools.chain(*topics.values()))

    # Letzten Stand aus Speicherdatei einlesen.
    if os.path.isfile(QUIZ_SAVE_FILE):
        with open(QUIZ_SAVE_FILE, "rb") as fp:
            save_point = pickle.load(fp)
            for s in save_point:
                identifier = s[0]
                correct_guess = s[1]
                false_guess = s[2]

                question = all_questions[identifier - 1]
                assert isinstance(question, Question)
                assert (
                    question.identifier == identifier
                ), f"Identifier nicht identisch {question.identifier} != {identifier}"
                question.correct_guess = correct_guess
                question.false_guess = false_guess

    while True:
        # Wähle eine Frage zufällig aus.
        # Je häufiger die Frage richtig beantwortet wurde, desto seltener
        # wird sie gewählt.
        question_weights = [q.weight for q in all_questions]
        question = random.choices(all_questions, weights=question_weights, k=1)[0]

        img = None
        if question.has_picture:
            img = mpimg.imread(question.picture_path)
            imgplot = plt.imshow(img)
            plt.show(block=False)

        guess = ask_question(question)

        if guess is True:
            question.correct_guess += 1
        elif guess is False:
            question.false_guess += 1
        elif guess is None:
            break
        else:
            raise NotImplementedError

        plt.close("all")

    # Stand in Speicherdatei sichern.
    save_point = [(q.identifier, q.correct_guess, q.false_guess) for q in all_questions]
    with open(QUIZ_SAVE_FILE, "wb") as fp:
        pickle.dump(save_point, fp)

    print_quiz_statistic(all_questions)
