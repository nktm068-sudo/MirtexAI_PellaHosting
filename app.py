import datetime
import os
import random
import re
import time
from flask import Flask, jsonify, render_template_string, request
import requests

app = Flask(__name__)

# 🔐 Секретная маскировка ссылок пробелами
WEATHER_URL_SPACED = "h t t p s : / / w t t r . i n / ? f o r m a t = j 1"
TRANSLATE_URL_SPACED = "h t t p s : / / t r a n s l a t e . g o o g l e a p i s . c o m / t r a n s l a t e _ a / s i n g l e ? c l i e n t = g t x & s l = r u & t l = e n & d t = t & q ="
INTERNET_URL_SPACED = "h t t p s : / / h t m l . d u c k d u c k g o . c o m / h t m l /"

user_chat_history = {}


def get_clean_url(spaced_url):
    return spaced_url.replace(" ", "")


def check_math(text):
    clean = re.sub(r"[^0-9+\-*/(). ]", "", text).strip()
    if len(clean) >= 3 and any(char.isdigit() for char in clean):
        try:
            code = compile(clean, "<string>", "eval")
            result = eval(code, {"__builtins__": {}}, {})
            if isinstance(result, (int, float)):
                return result
        except Exception:
            return None
    return None


def fetch_weather(city_name_ru=""):
    try:
        if not city_name_ru:
            city_name_ru = "Москва"
            city_name_en = "Moscow"
        else:
            city_name_ru = city_name_ru.strip().capitalize()
            clean_translate_url = (
                get_clean_url(TRANSLATE_URL_SPACED) + city_name_ru
            )
            tr_response = requests.get(clean_translate_url, timeout=5)
            city_name_en = tr_response.json()

        clean_url = get_clean_url(WEATHER_URL_SPACED).replace(
            "/?", f"/{city_name_en}?"
        )
        response = requests.get(clean_url, timeout=5)
        data = response.json()
        current = data["current_condition"]
        temp = current["temp_C"]

        desc = current.get("weatherDesc", [{"value": "Неизвестно"}])["value"]
        if "lang_ru" in current and current["lang_ru"]:
            desc = current["lang_ru"]["value"]

        return f"🌤 Погода в городе {city_name_ru}: Температура: {temp}°C. На улице: {desc}"
    except Exception:
        return "❌ Не удалось найти такой город. Проверь правильность названия!"


def ask_internet(query_text):
    try:
        from bs4 import BeautifulSoup

        clean_url = get_clean_url(INTERNET_URL_SPACED)
        user_agents_database = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        ]
        headers = {"User-Agent": random.choice(user_agents_database)}
        response = requests.post(
            clean_url, data={"q": query_text}, headers=headers, timeout=5
        )
        soup = BeautifulSoup(response.text, "html.parser")
        snippet = soup.find("a", class_="result__snippet")
        if snippet:
            return f"🌐 Вот что я нашёл в интернете: {snippet.text.strip()}"
    except Exception:
        pass
    return None


DATABASE = {
    "крипер": {
        "correct_name": "зеленая",
        "info": "Крипер — это культовый враждебный моб из игры Minecraft. Он имеет исключительно зелёную окраску для маскировки в траве. Розовых криперов в обычной игре не существует! 🟩",
    },
    "эндермен": {
        "correct_name": "черный",
        "info": "Эндермен — это высокий чёрный моб из измерения Энд. Он обладает способностью к телепортации. Его глаза светятся фиолетовым! ⬛",
    },
    "алмаз": {
        "correct_name": "голубой",
        "info": "Алмаз — один из самых ценных ресурсов в игре. Алмазная руда и сами алмазы имеют ярко-голубой оттенок. 💎",
    },
    "океан": {
        "correct_name": "соленый",
        "info": "Вода во всех мировых океанах является исключительно солёной. Пить такую воду без опреснения нельзя! 🌊",
    },
    "кола": {
        "correct_name": "черная",
        "info": "Классическая Кока-Кола имеет насыщенный тёмно-коричневый, практически чёрный цвет из-за добавления карамельного колера. 🥤",
    },
}

# 🖥️ Визуальный интерфейс сайта в одной переменной
HTML_INTERFACE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Миртекс ИИ Веб-Интерфейс</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #121212; color: #fff; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        h2 { color: #ff0055; text-shadow: 0 0 10px rgba(255,0,85,0.3); margin-bottom: 5px; }
        p.subtitle { color: #888; margin-top: 0; margin-bottom: 20px; font-size: 14px; }
        #chat-window { width: 480px; height: 420px; background: #1e1e1e; border-radius: 12px; padding: 15px; overflow-y: auto; box-shadow: 0 8px 24px rgba(0,0,0,0.6); display: flex; flex-direction: column; gap: 12px; border: 1px solid #2d2d2d; }
        .msg { padding: 10px 14px; border-radius: 10px; max-width: 80%; word-wrap: break-word; line-height: 1.4; font-size: 15px; }
        .user { background: #007bff; align-self: flex-end; color: #fff; box-shadow: 0 2px 5px rgba(0,123,255,0.2); }
        .bot { background: #2a2a2a; align-self: flex-start; color: #00ffcc; border: 1px solid #3a3a3a; }
        #input-area { display: flex; width: 512px; margin-top: 15px; gap: 10px; }
        input { flex: 1; padding: 12px; border-radius: 8px; border: 1px solid #333; background: #222; color: #fff; font-size: 15px; outline: none; }
        input:focus { border-color: #ff0055; }
        button { padding: 12px 24px; border: none; background: #ff0055; color: #fff; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 15px; transition: 0.2s; }
        button:hover { background: #dd0044; transform: scale(1.02); }
    </style>
</head>
<body>
    <h2>🤖 Веб-Ассистент Миртекс</h2>
    <p class="subtitle">С первым днём лета и началом каникул! ☀️</p>
    <div id="chat-window">
        <div class="msg bot">👋 Здравствуйте! Я ваш персональный ИИ-ассистент Миртекс. Я умею считать примеры, искать инфу в интернете и спорить про Майнкрафт! Чем могу помочь?</div>
    </div>
    <div id="input-area">
        <input type="text" id="user-msg" placeholder="Спроси меня о чём-нибудь..." onkeypress="if(event.key==='Enter') send()">
        <button onclick="send()">Отправить</button>
    </div>

    <script>
        function appendMessage(text, className) {
            const win = document.getElementById('chat-window');
            const div = document.createElement('div');
            div.className = 'msg ' + className;
            div.innerText = text;
            win.appendChild(div);
            win.scrollTop = win.scrollHeight;
        }

        async function send() {
            const input = document.getElementById('user-msg');
            const text = input.value.trim();
            if (!text) return;

            appendMessage(text, 'user');
            input.value = '';

            // Ставим лоадинг анимацию
            appendMessage('🧠 Миртекс думает...', 'bot');
            const win = document.getElementById('chat-window');
            const loadingMsgNode = win.lastChild;
            
            try {
                const response = await fetch('/get_response?text=' + encodeURIComponent(text));
                const data = await response.json();
                loadingMsgNode.innerText = data.reply;
            } catch (err) {
                loadingMsgNode.innerText = "❌ Ошибка соединения с сервером.";
            }
            win.scrollTop = win.scrollHeight;
        }
    </script>
</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML_INTERFACE)


@app.route("/get_response")
def get_response():
    text = request.args.get("text", "").lower().strip()
    ai_result = ""

    # Авто-проверка на др автора
    now_date = datetime.datetime.now()
    if now_date.day == 2 and now_date.month == 6:
        ai_result = "🎉 С Днем Рождения, Никита! (9 лет) 🥳 Пусть Xbox Series S тащит все игры на ультрах! Играй без багов!"
    else:
        if any(
            word in text
            for word in ["когда др", "день рождения автора", "др никиты"]
        ):
            ai_result = "📅 День рождения создателя бота празднуется 2 июня! 🎂"

    # 1. Счет
    if ai_result == "":
        math_result = check_math(text)
        if math_result is not None:
            ai_result = f"🧮 Ответ равен: {math_result}"

    # 2. Время
    if ai_result == "" and any(
        word in text for word in ["время", "час", "сколько время"]
    ):
        ai_result = (
            f"⏰ Время на сервере: {datetime.datetime.now().strftime('%H:%M:%S')}"
        )

    # 3. Погода
    if ai_result == "" and any(
        word in text for word in ["погода", "погоду", "на улице"]
    ):
        clean_text = text
        for trash in [
            "погода",
            "погоду",
            "на улице",
            "какая",
            "какой",
            "сейчас",
            "в",
            "на",
            "город",
            "городе",
        ]:
            clean_text = clean_text.replace(trash, "")
        ai_result = fetch_weather(clean_text.strip())

    # 4. Спор и инфа из базы
    if ai_result == "":
        found_topic = ""
        for key in DATABASE:
            if key in text:
                found_topic = key
                break
        if found_topic != "":
            topic_data = DATABASE[found_topic]
            correct_word = topic_data["correct_name"]
            main_info = topic_data["info"]
            wrong_words = [
                "розовый",
                "розовая",
                "белый",
                "белая",
                "красный",
                "синий",
                "зеленая",
                "зелёная",
                "соленый",
                "солёный",
                "черный",
                "чёрный",
                "голубой",
            ]
            has_correct_word = (
                correct_word in text
                or (correct_word == "зеленая" and "зелёная" in text)
                or (correct_word == "соленый" and "солёный" in text)
                or (correct_word == "черный" and "чёрный" in text)
            )
            user_speaks_about_color = any(word in text for word in wrong_words)

            if has_correct_word:
                ai_result = f"🤖 Да, всё верно! Ведь {main_info}"
            elif user_speaks_about_color:
                ai_result = f"Нет, вообще-то {found_topic} — *{correct_word}*, и вот почему: {main_info}"
            else:
                ai_result = f"📚 Вот информация по запросу: {main_info}"

    # 5. Парсинг интернета через Красивый Суп
    if ai_result == "":
        internet_reply = ask_internet(text)
        if internet_reply is not None:
            ai_result = internet_reply

    # 6. Обычный вежливый чат
    if ai_result == "":
        if any(word in text for word in ["привет", "хай", "ку", "салам"]):
            ai_result = "👋 Привет! Я твой веб-ассистент Миртекс. Как дела?"
        elif any(word in text for word in ["как дела", "как ты"]):
            ai_result = (
                "🚀 Все веб-системы работают стабильно на 100%! Как твои дела?"
            )
        else:
            ai_result = "🤖 Интересно! Не хочешь рассказать об этом поподробнее? Либо спроси меня что-то, чего я ещё не знаю!"

    return jsonify({"reply": ai_result})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
