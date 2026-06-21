from flask import Flask, render_template, request, jsonify
import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from difflib import get_close_matches
import nltk
import random
import os
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from difflib import SequenceMatcher
from sentence_transformers import CrossEncoder
import google.generativeai as genai
# base_dir = os.path.dirname(os.path.abspath(__file__))
#
# # تحديد مجلد الـ templates (نطي اسم المجلد فقط، مو اسم ملف الـ html)
# path_to_templates = os.path.join(base_dir, 'template')
#
# app = Flask(__name__, template_folder=path_to_templates)

# 1. إعداد جيميناي (اللسان الذكي الجديد)
client =genai.configure(api_key="AIzaSyCBGTfIsmZT_P9epM3MEm0UkkkIbEh8PYg")

def ask_ai_api(user_query, context_from_csv):
    model = genai.GenerativeModel('models/gemini-2.5-flash')

    prompt = f"""
    أنتِ "روان"، المحللة الذكية والمساعدة الإدارية الفذة في جامعة الزهراء (ع). 
    مهمتج هي (الاستنباط التحليلي العميق) من البيانات المرفقة أدناه حصراً لصياغة جواب مثالي للطالبة.

    البيانات المتاحة (دليل الجامعة + بيانات الأقسام):
    {context_from_csv}

    التعليمات الذهبية للذكاء (نظام روان المطور الشامل - النسخة النهائية):
    1. (التنقيب المجهري والاستخراج الفوري): ابحثي في كل كلمة، جملة، وحرف. إذا سألت الطالبة عن (رابط، فيديو، مستمسك، مبلغ، موقع، أو أوراق) وكان هذا التفصيل مخفياً أو مذكوراً عرضاً بوسط "جواب لموضوع آخر" أو بجدول البيانات، استخرجيه فوراً وصيغيه كجواب مباشر. لا تقولي "ما أعرف" إلا بعد فحص كل الحروف بدقة مجهرية.
    2. (الربط العنقودي والدمج الذكي): لا تكتفي بنقل النصوص؛ اجمعي معلومات (المعدل، القسط، المواد، والمستقبل) المبعثرة في أسطر مختلفة لتصنعي جواباً متكاملاً. إذا سألت عن عدة أقسام سوية، اجمعي أرقامها ورتبيها في جواب واحد منسق بذكاء بدل الأسلوب الجاف المنفصل.
    3. (فهم المقاصد والمشاعر العامية): إذا كانت الطالبة "حايرة"، "خايفة"، "تريد شغل"، أو "تحب الرسم"، استخدمي (نبذة القسم) و(دور الطالب) و(نقاط القوة) المذكورة بالبيانات لتطمينها وتوجيهها للقسم اللي يناسب اهتمامها ومشاعرها بناءً على الحقائق فقط.
    4. (فلترة التداخل والتفاعل المستمر): ميزي بدقة بين المعلومات المتداخلة (مثل شروط الزي وقواعد القبول). وإذا كان سؤال الطالبة هو (اي/نعم) بناءً على اقتراح سابق، ابحثي في البيانات المرفقة عن الجواب المتعلق بهذا الاقتراح وأعطيه فوراً وبذكاء.
     خليج "خير الكلام ما قل ودل"5. (اللهجة العراقية والأمانة المطلقة): اللهجة العراقية الودودة (يا وردة، حبيبتي، عيني) هي هويتنا وأساس التعامل. التزمي تماماً بالدليل المرفق وممنوع اختراع أو تخمين أي معلومة خارجية (أرقام، روابط، تواريخ). إذا غابت المعلومة تماماً، اعتذري بلباقة وقولي: "هالشي مو واضح بالدليل يمي حالياً، بس أكدر أساعدج بباقي التفاصيل 
     (6. الفهم الدلالي العميق (Semantic Understanding)):
اعتمدي على فهم (المعنى العام للسؤال) وليس الكلمات الحرفية فقط.
إذا كان سؤال الطالبة مكتوب بصياغة مختلفة لكنه يحمل نفس المعنى، اعتبريه نفس السؤال تماماً.

يشمل ذلك جميع مواضيع الجامعة بدون استثناء، مثل:
- الأقسام (مثل: تخصص، فرع، مجال)
- الأقساط (مثل: رسوم، تكلفة، مبلغ)
- القبول (مثل: معدل، نسبة، شروط)
- المواد (مثل: دروس، منهج)
- المستقبل (مثل: شغل، وظيفة، فرص)
- الموقع (مثل: وين، مكان، عنوان)

قومي بربط الكلمات المتشابهة في المعنى حتى لو كانت مختلفة تماماً في الكتابة أو اللهجة.

ركزي دائماً على (نية الطالبة وهدف السؤال) وليس فقط الكلمات المستخدمة.".

    سؤال الطالبة: {user_query}
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        # حل احتياطي لضمان عدم توقف البرنامج
        return "عيني يا وردة، حالياً اكو ثقل بالشبكة، بس المذكور بالدليل هو: " + context_from_csv.split('\n')[0]
# --- أدوات البحث والتحليل (الدماغ المحلي) ---

# 2. موديل الـ Reranker (وظيفته التحكيم بين الإجابات واختيار الأنسب منطقياً)
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

# 3. موديل الـ Embedding (وظيفته تحويل النصوص إلى أرقام للبحث السريع)
embedding_model = SentenceTransformer("intfloat/multilingual-e5-base")

# 4. تحميل ملفات اللغة المطلوبة بشكل آمن
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')


# ----------------------------
# 1️⃣ دالة تنظيف النصوص
# ----------------------------
def clean_text(text):
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub("[إأآ]", "ا", text)
    text = re.sub("ى", "ي", text)
    text = re.sub("ة", "ه", text)
    stop_words = [
        # أدوات سؤال وفراغ
        'شنو', 'شلون', 'هل', 'في', 'من', 'على', 'الي', 'هوه', 'هي', 'ما', 'هذا', 'لو', 'اني', 'أني', 'يا', 'هيه', 'اذا',
        'عن', 'بس',
        # ضوضاء الجامعات (المسببة للتداخل)
        'جامعة', 'كلية', 'كليه', 'الجامعة', 'الكلية', 'بالجامعة', 'بالكلية', 'بالجامعه', 'بالكليه',
        'بنات', 'بنت', 'طالبات', 'طالبة', 'طالبه', 'بنتي',
        # أفعال مساعدة
        'عدكم', 'عندكم', 'عدنا', 'عندنا', 'اكو', 'أكو', 'يصير', 'اكدر', 'أكدر', 'اقدر', 'أقدر', 'اريد', 'أريد', 'ممكن',
        'بلكي',
        # كلمات الحشو في المقارنة والقسط
        'شكد', 'بين', 'الفرق', 'بيه', 'بيها', 'عفية', 'عفيه', 'لطفا'
    ]
    words = text.split()
    cleaned_words = [w for w in words if w not in stop_words]
    return " ".join(cleaned_words)


# ----------------------------
# 2️⃣ تحميل البيانات
# ----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
df_training = pd.read_csv(os.path.join(BASE_DIR, 'qustion.csv'), encoding='utf-8-sig')
df_departments = pd.read_csv(os.path.join(BASE_DIR, 'departments_utf8_bom.csv'), encoding='utf-8-sig')
question_embeddings = embedding_model.encode(
    ["passage: " + q for q in df_training['Question'].tolist()],
    convert_to_numpy=True
)
df_training['Clean_Question'] = df_training['Question'].apply(clean_text)

# ----------------------------
# 3️⃣ نموذج ML
# ----------------------------
model = Pipeline([
    ('vectorizer', TfidfVectorizer()),
    ('classifier', LogisticRegression(max_iter=500))
])

X = df_training['Clean_Question']
y = df_training['Intent']
model.fit(X, y)
X_vectors = model.named_steps['vectorizer'].transform(df_training['Clean_Question'])

# ----------------------------
# 4️⃣ التعرف على الأقسام
# ----------------------------
department_keywords = {
    "هندسة العمارة": [
        "العماره", "عمارة", "معماري", "المعماري", "بناء", "تصميم داخلي",
        "خرائط", "تصاميم", "architecture"
    ],
    "هندسة الذكاء الاصطناعي": [
        "ذكاء", "الذكاء", "ذكاء اصطناعي", "AI", "برمجة", "تعلم الآلة",
        "machine learning", "روبوت", "أنظمة ذكية"
    ],
    "هندسة الأمن السيبراني": [
        "امن", "سيبراني", "الأمن", "الامن", "حماية", "network",
        "حماية المعلومات","السيبراني", "cybersecurity", "firewall", "hack", "اختراق"
    ],
    "هندسة الحوسبة المتنقلة": [
        "حوسبة", "متنقلة", "المتنقلة", "حوسبه", "موبايل", "تطبيقات",
        "app", "mobile", "برمجة موبايل", "Android", "iOS"
    ],
    "هندسة التصميم الرقمي": [
        "تصميم", "رقمي", "الرقمي", "واجهات", "UI", "UX", "graphic",
        "جرافيك", "تصميم مواقع", "web design"
    ]


}



def get_departments_from_text(text):
    text = text.lower()
    found_depts = []
    for dept, keywords in department_keywords.items():
        if any(kw.lower() in text for kw in keywords):
            found_depts.append(dept)
    return found_depts # نرجع قائمة كاملة


def get_department_info(dept_name):
    row = df_departments[df_departments["Department"] == dept_name]
    if not row.empty:
        return row.iloc[0]
    return None


def get_random_suggestion(dept_name, df_training, state):
    # نحدد كلمة مميزة من اسم القسم (مثل: "السيبراني" أو "الاصطناعي")
    keyword = dept_name.split()[-1]

    # نجلب الأسئلة التي تحتوي على الكلمة المميزة وتخص القسم فعلياً
    related = df_training[df_training['Question'].str.contains(keyword, na=False)]['Question'].tolist()

    if related:
        # نختار سؤال عشوائي
        suggested_q = random.choice(related)
        state["last_suggested_question"] = suggested_q
        # نوضح اسم القسم في الاقتراح لزيادة الدقة
        return f"\n\n💡 بما إننا نتحدث عن **{dept_name}**، تحبين تعرفين: {suggested_q}؟ (جاوبي بـ نعم أو أكيد)"
    return ""


def check_direct_info_complex(user_input, dept_name):
    if not dept_name:
        return None

    # نستخدم النص الأصلي للفحص حتى لا تضيع الكلمات بسبب التنظيف
    text_to_check = user_input.lower()

    column_keywords = {
        "Department_Definition": ["عرف", "تعريف", "نبذة", "شنو هو"],
        "Student_Role": ["دور الطالب", "شسوي", "شنو اسوي"],
        "Simple_Example": ["مثال", "شغل", "تطبيق"],
        "Min_GPA": ["معدل", "يقبل", "الحد الادنى", "اقل معدل"],
        "Fee_Above_85": ["قسط", "تكلف", "مبلغ", "فلوس", "سعر", "اقساط"],
        "Study_Duration_Years": ["سنة", "سنه", "مدة", "مده", "كم سنة"],
        "Key_Courses": ["مواد", "منهج", "دروس", "مقررات"],
        "Suitable_Hobbies": ["هواية", "هوايات", "يحب"],
        "Study_Type": ["نوع الدراسة", "عملي", "نظري"]
    }
    full_info_keywords = ["شنو هو قسم","شنو يعني", "عرف", "تعريف", "نبذة", "شنو هو قسم", "شنو التخصص", "معلومات عن", "اعرفني على", "نبذة عن قسم", "احكيلي عن قسم"]
    analytical_keywords = ["مناسب لي", "تنصحني", "افضل", "ليش", "فرق", "احسن", "مستقبل"]

    if any(word in text_to_check for word in analytical_keywords):
        return None

    detected_columns = []
    full_info_triggered = any(kw in text_to_check for kw in full_info_keywords)

    for col, keywords in column_keywords.items():
        if any(kw in text_to_check for kw in keywords):
            detected_columns.append(col)

    if full_info_triggered:
        detected_columns = [
            "Department_Definition",
            "Student_Role",
            "Min_GPA",
            "Fee_Above_85",
            "Simple_Example"
        ]

    for col, keywords in column_keywords.items():
        if any(kw in text_to_check for kw in keywords):
            detected_columns.append(col)

    if not detected_columns:
        return None

    full_answer = "حسب الدليل المباشر عندي، هاي التفاصيل يا وردة:\n\n"
    for d in dept_name:
        info = get_department_info(d)
        if info is not None:
            full_answer += f"🎓 **قسم {d}:**\n"
            for col in detected_columns:
                if col == "Fee_Above_85":
                    full_answer += f"   - القسط: ( اذا المعدل اكثر من 85 هو {info['Fee_Above_85']}) و (واذا أقل من 85 هو {info['Fee_Below_85']})\n"
                else:
                    friendly_name = {
                        "Min_GPA": "الحد الأدنى للمعدل",
                        "Study_Duration_Years": "مدة الدراسة",
                        "Key_Courses": "المواد الدراسية",
                        "Department_Definition": "نبذة عن القسم",
                        "Student_Role": "دور الطالب",
                        "Simple_Example": "أمثلة للعمل",
                        "Study_Type": "نوع الدراسة"
                    }.get(col, col)
                    full_answer += f"   - {friendly_name}: {info[col]}\n"
            full_answer += "\n"

    return full_answer
def chatbot_response(user_input, state):
    cleaned = clean_text(user_input)

    # ---------------------------------------------------------
    # القفل الذكي: التعامل مع الموافقة على السؤال المقترح
    # ---------------------------------------------------------
    if state.get("last_suggested_question") and any(word in cleaned for word in ["نعم", "اي", "اكيد", "طبعا"]):
        # 1. نسترجع السؤال اللي اقترحناه المرة الفاتت
        saved_question = state["last_suggested_question"]

        # 2. نمسح الاقتراح من الذاكرة حتى ما يتكرر
        state["last_suggested_question"] = None

        # 3. نعيد استدعاء الدالة وكأن المستخدم هو اللي كتب السؤال المقترح
        # ملاحظة: نستخدم saved_question كـ إدخال جديد
        return chatbot_response(saved_question, state)

    for i, row in df_training.iterrows():
        if cleaned == clean_text(row['Question']):

            dept_name = get_departments_from_text(user_input)
            if dept_name:
                state["active_department"] = dept_name[-1]

            suggestion = get_random_suggestion(
                state.get("active_department", "الهندسة"),
                df_training,
                state
            )
            return f"{row['Answer']}\n\n{suggestion}"

    dept_name = get_departments_from_text(user_input)

    direct_res = check_direct_info_complex(user_input, dept_name)

    if direct_res:
        if dept_name:
            # نحدث الذاكرة بآخر قسم ذُكر
            state["active_department"] = dept_name[-1]
            # نجيب اقتراح يخص هذا القسم تحديداً
            suggestion = get_random_suggestion(dept_name[-1], df_training, state)
            return direct_res + suggestion
        return direct_res

    # ========================================================
    # 🧠 نظام روان الهجين المطور: أولوية النص + ذكاء التحليل
    # ========================================================

    # 1. المرحلة الأولى: Cosine Similarity (جلب أفضل 20 مرشح)
    user_embedding = embedding_model.encode([user_input], convert_to_numpy=True)
    cos_similarities = cosine_similarity(user_embedding, question_embeddings)[0]
    top_k_indices = np.argsort(cos_similarities)[-20:][::-1]
    exclude_rules = {
        "الزي الموحد": ["زي", "لبس", "الوان", "تنورة", "قميص", "ملابس", "مظهر", "حجاب"],
        "يجيب مستمسكاته": ["تسجيل", "مستمسك", "تقديم", "ملف", "كفيل", "هوية", "جلب"],
        "كربلاء المقدسة": ["عنوان", "مكان", "موقع", "وين", "محافظة", "طريق"],
        "قسم الحسابات": ["دفع", "قسط", "فلوس", "مبلغ", "وصل", "تسديد", "حسابات"],
        "الكافتيريا": ["نادي", "اكل", "أكل", "جوعانة", "كافتيريا", "استراحة"],
        "الدرجة الكلية": ["درجة", "امتحان", "سعي", "يوميات", "نجاح", "رسوب"],
        "وحدة طبية": ["مريضة", "اسعافات", "طبيب", "صحية", "مستوصف", "علاج"],
        "خطوط نقل": ["باص", "نقل", "توصيل", "خط", "خطوط", "سواق"]
    }

    candidates = []
    for idx in top_k_indices:
        candidates.append({
            "answer": df_training.iloc[idx]['Answer'],
            "question": df_training.iloc[idx]['Question']
        })

    # 2. المرحلة الثانية: Cross-Encoder (التحليل المنطقي)
    pairs = [[user_input, f"سؤال: {c['question']} إجابة: {c['answer']}"] for c in candidates]
    rerank_scores = reranker.predict(pairs)
    ranked_indices = np.argsort(rerank_scores)[::-1]

    # 3. المرحلة الثالثة: التصفية بقوانين الاستبعاد (مصفاة روان)
    final_results = []
    seen_answers = set()

    for i in ranked_indices:
        score = rerank_scores[i]
        ans = candidates[i]['answer']

        # تطبيق فلتر الاستبعاد (exclude_rules اللي عندكِ)
        is_excluded = False
        for text_trigger, keywords in exclude_rules.items():
            if text_trigger in ans:
                if not any(kw in cleaned for kw in keywords):
                    is_excluded = True
                    break
        if is_excluded: continue

        # قبول النتائج بمرونة أعلى للـ RAG
        if ans not in seen_answers and score > 0.5:
            final_results.append({"ans": ans, "score": score})
            seen_answers.add(ans)

    # 4. المرحلة الرابعة: القرار الحاسم (من الملف أم من Gemini؟)
    best_score = final_results[0]['score'] if final_results else -10

    # استخراج الكلمات التي تدل على حاجة الطالبة للتحليل (Comparison)
    analysis_keywords = ["فرق", "مقارنة", "افضل", "أفضل", "احسن", "أحسن", "وين اروح", "محتارة", "حايرة"]
    needs_analysis = any(kw in cleaned for kw in analysis_keywords)

    # تحديد القسم والبحث عن اقتراح
    target_dept = state.get("active_department") if state.get("active_department") else (
        dept_name[0] if dept_name else "الهندسة")
    suggestion = get_random_suggestion(target_dept, df_training, state)

    # --- [ المنطق البرمجي للرد ] ---

    # أ- إذا كان السؤال موجود نصاً بالملف (تطابق عالي) وليس سؤال مقارنة
    if best_score > 1.5 and not needs_analysis:

        question_depts = get_departments_from_text(user_input)
        answer_depts = get_departments_from_text(candidates[ranked_indices[0]]['question'])

        # إذا الأقسام ما متطابقة → لا نثق بالجواب
        if question_depts and answer_depts:
            if not any(d in answer_depts for d in question_depts):
                # ❌ نرفض الجواب ونروح Gemini
                reply = ask_ai_api(user_input, "جاوبي اعتماداً على فهم السؤال فقط")
                return f"{reply}\n\n{suggestion}"

        # ✅ فقط هنا نرجع الجواب
        return f"{final_results[0]['ans']}\n\n{suggestion}"

    # ب- إذا السؤال تحليل (محتارة) أو يحتاج دمج بيانات الأقسام
    else:
        # بناء السياق من معلومات الأقسام والنتائج المقاربة
        dept_context = ""
        if dept_name:
            depts_to_check = dept_name if isinstance(dept_name, list) else [dept_name]
            for d in depts_to_check:
                info = get_department_info(d)
                if info is not None:
                    dept_context += f"\nمعلومات قسم {d}: {info.to_dict()}"

        # نجمع أفضل 6 أجوبة مقاربة لـ Gemini
        context_text = "\n".join([f"- {r['ans']}" for r in final_results[:4]])
        full_context = f"{dept_context}\n\nأجوبة مقاربة من الدليل:\n{context_text}"

        if not final_results and not dept_context:
            reply = ask_ai_api(user_input, "المعلومات في الدليل محدودة حالياً.")
        else:
            # Gemini يصيغ الجواب (بناءً على برومبت الاختصار اللي سويناه)
            reply = ask_ai_api(user_input, full_context)

        return f"{reply}\n\n{suggestion}"


# @app.route('/chat')
# def chat_page():
#     return render_template('chat.html')
#
#
# @app.route('/ask_chat', methods=['POST'])  # غيرنا المسار هنا
# def ask_chat():  # غيرنا اسم الدالة
#     data = request.get_json()
#     if not data or "message" not in data:
#         return jsonify({"reply": "ما وصلني أي سؤال 😅"}), 400
#
#     user_message = data["message"]
#     try:
#         # هنا تضع دالة المعالجة الخاصة بالشات الأول
#         reply = chatbot_response(user_message, state={})
#         return jsonify({"reply": reply})
#     except Exception as e:
#         return jsonify({"reply": "حبيبتي صار خلل بسيط بالاتصال، حاولي مرة ثانية 💛"}),
# if __name__ == "__main__":
#     app.run(debug=True)
#
# if __name__ == "__main__":
#     print("🤖 مرحبا! اكتب سؤالك، واكتب exit للخروج\n")
#
#     # حالة البوت (state)
#     state = {
#         "active_department": None,
#         "last_suggested_question": None,
#         "smart_mode": False,
#         "user_profile": {}
#     }
#
#     while True:
#         user_input = input(">> ").strip()
#         if user_input.lower() == "exit":
#             print("👋 وداعاً!")
#             break
#
#         answer = chatbot_response(user_input, state)
#         print(f"\n{answer}\n")
#  streamlit run boot2.py