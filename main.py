"""Mission 2: Python 객체지향 콘솔 퀴즈 게임 (Python 3.10+)."""

import json
import random
from datetime import datetime
from pathlib import Path

STATE_FILE = Path(__file__).resolve().parent / "state.json"
HINT_PENALTY = 10


class Quiz:
    """문제 하나의 데이터와 정답 확인 기능을 담당한다."""

    def __init__(self, question, choices, answer, hint=""):
        if not isinstance(question, str) or not question.strip():
            raise ValueError("문제는 빈 문자열일 수 없습니다.")
        if (not isinstance(choices, list) or len(choices) != 4
                or any(not isinstance(c, str) or not c.strip() for c in choices)):
            raise ValueError("선택지는 비어 있지 않은 문자열 4개여야 합니다.")
        if type(answer) is not int or not 1 <= answer <= 4:
            raise ValueError("정답 번호는 1~4 사이의 정수여야 합니다.")
        if not isinstance(hint, str):
            raise ValueError("힌트는 문자열이어야 합니다.")
        self.question = question.strip()
        self.choices = [choice.strip() for choice in choices]
        self.answer = answer
        self.hint = hint.strip()

    def display(self):
        print(f"\n{self.question}")
        for number, choice in enumerate(self.choices, start=1):
            print(f"  {number}. {choice}")

    def check_answer(self, user_answer):
        return self.answer == user_answer

    def to_dict(self):
        return {
            "question": self.question,
            "choices": self.choices,
            "answer": self.answer,
            "hint": self.hint,
        }

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ValueError("퀴즈 데이터는 객체여야 합니다.")
        return cls(data["question"], data["choices"], data["answer"],
                   data.get("hint", ""))


class QuizGame:
    """메뉴, 게임 진행, 입력 검증, 점수, JSON 저장을 관리한다."""

    def __init__(self):
        self.quizzes = []
        self.best_score = None
        self.history = []
        self.load_data()

    @staticmethod
    def default_quizzes():
        return [
            Quiz("Python에서 정수를 나타내는 자료형은?",
                 ["str", "int", "bool", "list"], 2, "integer의 약자입니다."),
            Quiz("여러 값을 순서대로 저장하는 자료형은?",
                 ["dict", "bool", "list", "int"], 3, "대괄호 []를 사용합니다."),
            Quiz("조건에 따라 실행 경로를 선택하는 키워드는?",
                 ["for", "if", "def", "class"], 2, "영어로 '만약'이라는 뜻입니다."),
            Quiz("Python에서 함수를 정의하는 키워드는?",
                 ["return", "import", "while", "def"], 4, "define의 줄임말입니다."),
            Quiz("JSON 파일을 읽고 Python 객체로 변환하는 함수는?",
                 ["json.load", "json.dump", "print", "input"], 1,
                 "파일에서 데이터를 불러오는 load를 생각하세요."),
        ]

    @staticmethod
    def read_text(prompt, allow_empty=False):
        while True:
            value = input(prompt).strip()
            if value or allow_empty:
                return value
            print("⚠️ 빈 입력은 허용되지 않습니다. 다시 입력하세요.")

    @staticmethod
    def read_number(prompt, minimum, maximum):
        while True:
            raw = input(prompt).strip()
            if not raw:
                print("⚠️ 빈 입력입니다. 숫자를 입력하세요.")
                continue
            try:
                value = int(raw)
            except ValueError:
                print(f"⚠️ 숫자만 입력하세요. ({minimum}~{maximum})")
                continue
            if minimum <= value <= maximum:
                return value
            print(f"⚠️ {minimum}~{maximum} 사이의 숫자를 입력하세요.")

    def load_data(self):
        if not STATE_FILE.exists():
            self.quizzes = self.default_quizzes()
            print("📂 저장 파일이 없어 기본 퀴즈 5개로 시작합니다.")
            return
        try:
            with STATE_FILE.open("r", encoding="utf-8") as file:
                data = json.load(file)
            if not isinstance(data, dict) or not isinstance(data.get("quizzes"), list):
                raise ValueError("quizzes 필드가 올바르지 않습니다.")
            quizzes = [Quiz.from_dict(item) for item in data["quizzes"]]
            best_score = data.get("best_score")
            if best_score is not None and (type(best_score) is not int
                                           or not 0 <= best_score <= 100):
                raise ValueError("best_score 값이 올바르지 않습니다.")
            history = data.get("history", [])
            if not isinstance(history, list) or any(not isinstance(h, dict) for h in history):
                raise ValueError("history 값이 올바르지 않습니다.")
            self.quizzes, self.best_score, self.history = quizzes, best_score, history
            print(f"📂 저장된 데이터를 불러왔습니다. (퀴즈 {len(quizzes)}개, 기록 {len(history)}건)")
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError, KeyError, TypeError) as exc:
            print(f"⚠️ 저장 파일을 읽을 수 없습니다: {exc}")
            # 원본을 잃지 않도록 손상된 파일을 별도로 보관한다.
            try:
                backup = STATE_FILE.with_name(
                    f"state.corrupt.{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json")
                STATE_FILE.replace(backup)
                print(f"📦 기존 파일 보관: {backup.name}")
            except OSError as backup_error:
                print(f"⚠️ 원본 파일 보관 실패: {backup_error}")
                print("⚠️ 기존 파일을 보호하기 위해 이번 실행에서는 저장을 중단합니다.")
                self._save_disabled = True
            self.quizzes = self.default_quizzes()
            self.best_score = None
            self.history = []
            print("📂 기본 퀴즈로 복구하여 시작합니다.")

    def save_data(self):
        if getattr(self, "_save_disabled", False):
            print("⚠️ 원본 파일 보호를 위해 저장하지 않았습니다.")
            return False
        data = {
            "quizzes": [quiz.to_dict() for quiz in self.quizzes],
            "best_score": self.best_score,
            "history": self.history,
        }
        temp_file = STATE_FILE.with_name("state.tmp")
        try:
            with temp_file.open("w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
            temp_file.replace(STATE_FILE)
            return True
        except OSError as exc:
            print(f"⚠️ 데이터 저장 실패: {exc}")
            try:
                temp_file.unlink(missing_ok=True)
            except OSError:
                pass
            return False

    @staticmethod
    def show_menu():
        print("\n" + "=" * 42)
        print("       🎯 Python 퀴즈 게임 🎯")
        print("=" * 42)
        print("1. 퀴즈 풀기")
        print("2. 퀴즈 추가")
        print("3. 퀴즈 목록")
        print("4. 최고 점수 확인")
        print("5. 퀴즈 삭제 (보너스)")
        print("6. 점수 기록 히스토리 (보너스)")
        print("7. 종료")
        print("=" * 42)

    def play_quiz(self):
        if not self.quizzes:
            print("⚠️ 등록된 퀴즈가 없습니다. 먼저 퀴즈를 추가하세요.")
            return
        count = self.read_number(
            f"출제할 문제 수 (1~{len(self.quizzes)}): ", 1, len(self.quizzes))
        selected = random.sample(self.quizzes, count)
        correct = 0
        hints_used = 0
        print(f"\n📝 퀴즈를 시작합니다! (총 {count}문제, 순서 무작위)")
        for index, quiz in enumerate(selected, start=1):
            print("\n" + "-" * 42)
            print(f"[문제 {index}/{count}]")
            quiz.display()
            if quiz.hint:
                use_hint = self.read_number("힌트를 보시겠습니까? (1: 예, 2: 아니요): ", 1, 2)
                if use_hint == 1:
                    print(f"💡 힌트: {quiz.hint} (최종 점수에서 {HINT_PENALTY}점 차감)")
                    hints_used += 1
            answer = self.read_number("정답 번호 (1~4): ", 1, 4)
            if quiz.check_answer(answer):
                correct += 1
                print("✅ 정답입니다!")
            else:
                print(f"❌ 오답입니다. 정답은 {quiz.answer}번입니다.")
        base_score = round(correct / count * 100)
        score = max(0, base_score - hints_used * HINT_PENALTY)
        record = {
            "played_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "total_questions": count,
            "correct_answers": correct,
            "hints_used": hints_used,
            "score": score,
        }
        self.history.append(record)
        is_new_best = self.best_score is None or score > self.best_score
        if is_new_best:
            self.best_score = score
        print("\n" + "=" * 42)
        print(f"🏆 결과: {count}문제 중 {correct}문제 정답")
        print(f"기본 점수 {base_score}점 - 힌트 감점 {hints_used * HINT_PENALTY}점 = {score}점")
        if is_new_best:
            print("🎉 새로운 최고 점수입니다!")
        print("=" * 42)
        self.save_data()

    def add_quiz(self):
        print("\n📌 새로운 퀴즈를 추가합니다.")
        question = self.read_text("문제: ")
        choices = [self.read_text(f"선택지 {i}: ") for i in range(1, 5)]
        answer = self.read_number("정답 번호 (1~4): ", 1, 4)
        hint = self.read_text("힌트 (없으면 Enter): ", allow_empty=True)
        self.quizzes.append(Quiz(question, choices, answer, hint))
        if self.save_data():
            print("✅ 퀴즈를 추가하고 저장했습니다.")
        else:
            print("⚠️ 퀴즈는 현재 실행에만 추가되었습니다. 저장 상태를 확인하세요.")

    def list_quizzes(self):
        if not self.quizzes:
            print("⚠️ 등록된 퀴즈가 없습니다.")
            return
        print(f"\n📋 등록된 퀴즈 목록 (총 {len(self.quizzes)}개)")
        for index, quiz in enumerate(self.quizzes, start=1):
            print(f"{index}. {quiz.question}")

    def show_best_score(self):
        if self.best_score is None:
            print("🏆 아직 퀴즈를 푼 기록이 없습니다.")
        else:
            print(f"🏆 최고 점수: {self.best_score}점 / 100점")

    def delete_quiz(self):
        if not self.quizzes:
            print("⚠️ 삭제할 퀴즈가 없습니다.")
            return
        self.list_quizzes()
        number = self.read_number(
            f"삭제할 퀴즈 번호 (1~{len(self.quizzes)}): ", 1, len(self.quizzes))
        print(f"선택한 문제: {self.quizzes[number - 1].question}")
        confirm = self.read_number("정말 삭제하시겠습니까? (1: 삭제, 2: 취소): ", 1, 2)
        if confirm == 2:
            print("삭제를 취소했습니다.")
            return
        removed = self.quizzes.pop(number - 1)
        if self.save_data():
            print(f"🗑️ 삭제 및 저장 완료: {removed.question}")
        else:
            print("⚠️ 현재 실행에서만 삭제되었습니다. 저장 상태를 확인하세요.")

    def show_history(self):
        if not self.history:
            print("📜 아직 저장된 게임 기록이 없습니다.")
            return
        print(f"\n📜 게임 기록 (총 {len(self.history)}건)")
        for index, record in enumerate(self.history, start=1):
            print(f"{index}. {record.get('played_at', '날짜 미상')} | "
                  f"{record.get('total_questions', '?')}문제 중 "
                  f"{record.get('correct_answers', '?')}개 정답 | "
                  f"힌트 {record.get('hints_used', 0)}회 | "
                  f"{record.get('score', '?')}점")

    def run(self):
        try:
            while True:
                self.show_menu()
                choice = self.read_number("선택 (1~7): ", 1, 7)
                if choice == 1:
                    self.play_quiz()
                elif choice == 2:
                    self.add_quiz()
                elif choice == 3:
                    self.list_quizzes()
                elif choice == 4:
                    self.show_best_score()
                elif choice == 5:
                    self.delete_quiz()
                elif choice == 6:
                    self.show_history()
                else:
                    print("👋 게임을 종료합니다.")
                    break
        except (KeyboardInterrupt, EOFError):
            print("\n⚠️ 입력이 중단되었습니다. 가능한 데이터를 저장하고 안전하게 종료합니다.")
        finally:
            self.save_data()


if __name__ == "__main__":
    QuizGame().run()
