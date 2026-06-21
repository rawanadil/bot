from flask import Flask, request, jsonify, render_template
from boot2 import chatbot_response, client
from future_engineer_bot import MODEL_ID, SYSTEM_PROMPT
app = Flask(__name__, template_folder='template')

# ================== CHAT ==================
state={}
@app.route('/chat')
def chat_page():
    return render_template('chat.html')
@app.route('/ask_chat', methods=['POST'])
def ask_chat():
    data = request.get_json()
    user_message = data.get("message")

    reply = chatbot_response(user_message, state)
    return jsonify({"reply": reply})

@app.route('/ee.html')
def ee_page():
    return render_template('ee.html')
#
# # ================== PAS ==================
@app.route('/pas')
def home():
    return render_template('general_faq2.html')

@app.route('/ask_pas', methods=['POST']) # مسار مختلف تماماً
def ask_pas(): # اسم دالة مختلف
    data = request.get_json()
    user_message = data.get("message")
    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=f"{SYSTEM_PROMPT}\n\nسؤال الطالبة: {user_message}"
        )
        return jsonify({"reply": response.text})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"reply": "حبيبتي صارت مشكلة صغيرة بالاتصال، حاولي مرة ثانية."})

# ================== RUN ==================
if __name__ == "__main__":
    app.run(debug=True)