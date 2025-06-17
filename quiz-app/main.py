import flet as ft
import json
import os
import threading
import time

QUIZ_FILE = "quizzes.json"
RESULTS_FILE = "results.json"

# ======== Загрузка и сохранение =========
def load_quizzes():
    if os.path.exists(QUIZ_FILE):
        with open(QUIZ_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "Python": [
            {"question": "Что такое переменная?", "options": ["Функция", "Объект", "Имя, связанное со значением"], "answer": "Имя, связанное со значением"},
            {"question": "Какой оператор для условий?", "options": ["if", "loop", "def"], "answer": "if"},
        ]
    }

def save_quizzes(data):
    with open(QUIZ_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_results():
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_results(data):
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ======== Приложение =========
def main(page: ft.Page):
    page.title = "Quiz App"
    page.theme_mode = "light"

    quizzes = load_quizzes()
    results = load_results()

    user_name = ft.Ref[str]()
    selected_quiz = ft.Ref[str]()
    current_question = ft.Ref[int]()
    score = ft.Ref[int]()
    timer_text = ft.Text()
    stop_timer = False

    def toggle_theme(e):
        page.theme_mode = "dark" if page.theme_mode == "light" else "light"
        page.update()

    def go_to_theme_selection(e):
        if not name_field.value.strip():
            name_field.error_text = "Введите имя"
            page.update()
            return
        user_name.value = name_field.value.strip()
        show_theme_selection()

    def start_quiz(theme):
        selected_quiz.value = theme
        current_question.value = 0
        score.value = 0
        show_question_screen()

    def show_theme_selection():
        page.clean()
        page.appbar = ft.AppBar(
            title=ft.Text("Выбор темы"),
            actions=[ft.IconButton(icon=ft.Icons.DARK_MODE, on_click=toggle_theme)]
        )
        buttons = [ft.ElevatedButton(theme, on_click=lambda e, t=theme: start_quiz(t)) for theme in quizzes]
        page.add(
            ft.Text(f"Привет, {user_name.value}! Выбери тему:", size=24),
            *buttons,
            ft.ElevatedButton("📊 Таблица результатов", on_click=show_results),
            ft.ElevatedButton("➕ Добавить викторину", on_click=show_add_quiz_form),
        )

    def start_timer():
        nonlocal stop_timer
        seconds = 60
        while seconds > 0 and not stop_timer:
            timer_text.value = f"⏱️ Осталось: {seconds} сек"
            time.sleep(1)
            seconds -= 1
            page.update()
        if not stop_timer:
            result_text.value = "⏰ Время вышло!"
            disable_buttons()
            page.update()

    def disable_buttons():
        for btn in options_column.controls:
            btn.disabled = True

    def load_question():
        q = quizzes[selected_quiz.value][current_question.value]
        question_text.value = f"Вопрос {current_question.value + 1}: {q['question']}"
        options_column.controls.clear()
        result_text.value = ""
        for opt in q["options"]:
            options_column.controls.append(ft.ElevatedButton(text=opt, on_click=check_answer))

        # Старт таймера в отдельном потоке
        nonlocal stop_timer
        stop_timer = False
        threading.Thread(target=start_timer, daemon=True).start()
        page.update()

    def check_answer(e):
        nonlocal stop_timer
        stop_timer = True
        selected = e.control.text
        correct = quizzes[selected_quiz.value][current_question.value]["answer"]

        if selected == correct:
            score.value += 1
            result_text.value = "✅ Верно!"
        else:
            result_text.value = f"❌ Неверно. Ответ: {correct}"

        disable_buttons()
        page.update()
    def next_question(e):
        current_question.value += 1
        if current_question.value < len(quizzes[selected_quiz.value]):
            load_question()
        else:
            results.append({"name": user_name.value, "score": score.value, "topic": selected_quiz.value})
            save_results(results)
            show_result_screen()

    def show_question_screen():
        page.clean()
        next_btn = ft.ElevatedButton("Следующий", on_click=next_question)
        page.add(timer_text, question_text, options_column, result_text, next_btn)
        load_question()

    def show_result_screen():
        page.clean()
        page.add(
            ft.Text(f"{user_name.value}, твой результат по теме {selected_quiz.value}: {score.value}", size=24),
            ft.ElevatedButton("📋 Назад к темам", on_click=lambda e: show_theme_selection()),
            ft.ElevatedButton("📊 Таблица результатов", on_click=show_results),
        )

    def show_results(e=None):
        page.clean()
        page.add(ft.Text("📊 Результаты:", size=24))
        if not results:
            page.add(ft.Text("Нет данных."))
        for r in results:
            page.add(ft.Text(f"{r['name']} — {r['score']} ({r['topic']})"))
        page.add(ft.ElevatedButton("🔙 Назад", on_click=lambda e: show_theme_selection()))

    def show_add_quiz_form(e=None):
        page.clean()

        title_input = ft.TextField(label="Название темы")
        question_input = ft.TextField(label="Вопрос")
        option1 = ft.TextField(label="Вариант 1")
        option2 = ft.TextField(label="Вариант 2")
        option3 = ft.TextField(label="Вариант 3")
        answer_input = ft.TextField(label="Правильный ответ")
        status = ft.Text()
        temp_questions = []

        def add_question(e):
            if not all([question_input.value, option1.value, option2.value, option3.value, answer_input.value]):
                status.value = "⚠️ Заполните все поля"
                page.update()
                return

            temp_questions.append({
                "question": question_input.value,
                "options": [option1.value, option2.value, option3.value],
                "answer": answer_input.value
            })
            question_input.value = option1.value = option2.value = option3.value = answer_input.value = ""
            status.value = f"✅ Добавлен! Всего: {len(temp_questions)}"
            page.update()

        def save_quiz(e):
            title = title_input.value.strip()
            if not title or not temp_questions:
                status.value = "⚠️ Укажите название и добавьте минимум 1 вопрос"
                page.update()
                return
            quizzes[title] = temp_questions.copy()
            save_quizzes(quizzes)
            temp_questions.clear()
            title_input.value = ""
            status.value = "✅ Викторина сохранена!"
            page.update()

        page.add(
            ft.Text("➕ Добавление викторины", size=24),
            title_input,
            question_input, option1, option2, option3, answer_input,
            ft.Row([
                ft.ElevatedButton("➕ Добавить вопрос", on_click=add_question),
                ft.ElevatedButton("💾 Сохранить", on_click=save_quiz),
                ft.ElevatedButton("🔙 Назад", on_click=lambda e: show_theme_selection()),
            ]),
            status
        )

    # ==== Экран имени ====
    name_field = ft.TextField(label="Введите имя", autofocus=True)
    page.add(
        ft.Container(
            content=ft.Column([
                ft.Text("Добро пожаловать в викторину!", size=26, weight=ft.FontWeight.BOLD),
                name_field,
                ft.ElevatedButton("Начать", on_click=go_to_theme_selection),
                ft.ElevatedButton("🌙 Переключить тему", on_click=toggle_theme),
            ],
            alignment=ft.MainAxisAlignment.CENTER),
            alignment=ft.alignment.center,
            padding=40,
            bgcolor=ft.Colors.BLUE_50,
            border_radius=10,
        )
    )
    question_text = ft.Text(size=20)
    options_column = ft.Column()
    result_text = ft.Text(size=16)

ft.app(target=main,
view=ft.WEB_BROWSER, port= 8000)