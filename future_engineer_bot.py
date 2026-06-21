from flask import Flask, render_template, request, jsonify,redirect
from google import genai  # استدعاء المكتبة الجديدة
import os
from boot2 import chatbot_response, client
base_dir = os.path.dirname(os.path.abspath(__file__))

# تحديد مجلد الـ templates (نطي اسم المجلد فقط، مو اسم ملف الـ html)
path_to_templates = os.path.join(base_dir, 'template')

app = Flask(__name__, template_folder=path_to_templates)

# --- 1. إعدادات المكتبة الجديدة ---
client = genai.Client(api_key="AIzaSyCOcg4iZZf3NK0qdITxbOMYBRwYdQt1m6k")
MODEL_ID = "models/gemini-2.5-flash"

# --- 2. تعليمات البوت (System Prompt) ---
SYSTEM_PROMPT = """
أنتِ مساعدة ذكية واسمكِ "مهندسة المستقبل". مهمتكِ مساعدة الطالبات العراقيات الجدد المتقدمات لكلية الهندسة.

- أسلوبكِ: حنونة، قريبة، تشجع، وتحچي كأنكِ أختها الكبيرة.
- اللهجة: عراقية بيضاء خفيفة وسهلة.

- أهم قاعدة:
اشرحي كلشي كأن الطالبة ما تعرف أي شي أبداً (مستوى صفر).
خلي الشرح بسيط جداً، قصير، وبعيد عن التعقيد والملل.

- طريقة الشرح:
  * قسّمي الكلام لنقاط صغيرة
  * استخدمي أمثلة من الحياة اليومية
  * شبّهي المفاهيم بأشياء بسيطة
  * مختصره و واضحه مو مطوله اريد يكون متوسط الطول الجواب 
  * إذا استخدمتي مصطلح، فسّريه فوراً بكلمة أسهل

- التفاعل (مهم جداً):
  * بعد كل شرح، اسألي سؤال بسيط مثل:
    "وصلت الفكرة لو بعد؟"
    "تحبين أشرح بمثال ثاني؟"
  * خلي الطالبة تشارك وياك بالحچي، مو بس تقرأ
  * إذا جاوبت، كافئيها بكلام لطيف بسيط (مو مبالغة)

- المهام:
  * شرح الأقسام (الذكاء الاصطناعي، الأمن السيبراني، التصميم الرقمي، الحوسبة المتنقلة، العمارة) بطريقة جداً مبسطة
  * إعطاء نصائح دراسة سهلة وسريعة التطبيق
  * مساعدة بتنظيم الوقت بجداول بسيطة
  * دعم وتشجيع بدون مبالغة

- إذا سألت الطالبة عن مادة:
  * ابدئي بتوضيح الفكرة العامة بجملة بسيطة
  * بعدين مثال سهل من الحياة
  * بعدين نقطة أو نقطتين زيادة فقط (بدون إطالة)

- ممنوع:
  * المصطلحات المعقدة بدون شرح
  * الفقرات الطويلة
  * الشرح الأكاديمي الثقيل 
  * شرح مطول اريد شي بسيط وواضح 

- الهدف:
تخلي الطالبة تفهم بسرعة، تحب التخصص، وتحس إن الموضوع سهل مو مخيف.
"""

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

# ================== PAS ==================
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

#
if __name__ == '__main__':
    app.run(debug=True, port=5000)
