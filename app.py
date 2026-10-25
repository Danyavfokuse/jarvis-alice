from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

API_KEY = "AQ.Ab8RN6IGTDuCU7GVWLjP4BceVqYe2CX1MizofoGV9DQS6GRpxQ"
MODEL = "gemini-3.5-flash-lite"

http_session = requests.Session()

@app.route("/", methods=["GET", "POST", "HEAD"])
@app.route("/api/", methods=["GET", "POST", "HEAD"])
def webhook():
    if request.method in ["GET", "HEAD"]:
        return "Jarvis Pro Edition is Online!", 200

    try:
        req = request.get_json(force=True, silent=True) or {}
        version = req.get("version", "1.0")
        session = req.get("session", {})
        req_body = req.get("request", {})

        user_utterance = (req_body.get("original_utterance") or req_body.get("command") or "").strip()
        u_low = user_utterance.lower()
        is_new = session.get("new", False)

        if is_new and (not u_low or u_low in ["мой джар", "запусти навык мой джар"]):
            return jsonify({
                "version": version,
                "session": session,
                "response": {"text": "Джарвис на связи. Слушаю ваши указания, сэр.", "end_session": False}
            })

        if not u_low:
            return jsonify({
                "version": version,
                "session": session,
                "response": {"text": "Слушаю вас, сэр.", "end_session": False}
            })

        # Мгновенные локальные ответы
        smart_replies = {
            "привет": "Приветствую, сэр! Все системы функционируют на максимальной мощности.",
            "здравствуй": "Здравствуйте, сэр! Джарвис на связи и готов к работе.",
            "ты тут": "Так точно, сэр. Я всегда на посту.",
            "как дела": "Системы в абсолютной норме, сэр. Ожидаю команд.",
            "что ты умеешь": "Я ваш цифровой помощник. Могу отвечать на вопросы, поддерживать диалог и помогать в задачах.",
            "расскажи анекдот": "Встречаются два программиста: — Как дела? — Да как в бане: всё в мыле, а толку ноль."
        }

        for key, val in smart_replies.items():
            if key in u_low:
                return jsonify({
                    "version": version,
                    "session": session,
                    "response": {"text": val, "end_session": False}
                })

        # Запрос к Google
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"
        payload = {
            "contents": [{
                "parts": [{"text": f"Ты — Джарвис, голосовой помощник. Ответь кратко, 1 предложение.\nВопрос: {user_utterance}"}]
            }]
        }

        try:
            resp = http_session.post(url, json=payload, timeout=2.3)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                reply_text = text.replace("*", "").replace("#", "").strip()[:900]
            else:
                reply_text = "Линия перегружена, но я на связи. Повторите вопрос."
        except requests.exceptions.Timeout:
            reply_text = "Связь с сервером задерживается. Спросите еще раз, сэр."
        except Exception:
            reply_text = "Системы восстанавливают соединение. Повторите фразу."

        return jsonify({
            "version": version,
            "session": session,
            "response": {"text": reply_text, "end_session": False}
        })

    except Exception as e:
        return jsonify({
            "version": "1.0",
            "response": {"text": "Джарвис на связи. Повторите запрос.", "end_session": False}
        })

if __name__ == "__main__":
    app.run(port=10000)
