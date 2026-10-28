import streamlit as st

# --- 1. إعدادات الصفحة والتصميم المتناسق ---
st.set_page_config(page_title="المساعد الذكي - الاختبار", layout="centered")

st.markdown("""
    <style>
    /* تغيير الخلفية لتناسب الصفحة الرئيسية */
    .stApp { 
        background-color: #f6fafe; 
    }

    /* تصميم فقاعة كلام البوت */
    .bot_msg {
        background-color: white;
        color: #004659;
        padding: 25px;
        border-radius: 20px;
        margin-bottom: 25px;
        text-align: right;
        font-size: 1.1rem;
        line-height: 1.8;
        border-right: 6px solid #155e75;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        direction: rtl;
    }

    /* تصميم الأزرار لتشبه أزرار الصفحة الرئيسية */
    .stButton>button {
        width: 100%;
        background-color: #004659 !important;
        color: white !important;
        border-radius: 12px;
        height: 3.5em;
        font-size: 1.1em !important;
        font-weight: bold;
        transition: all 0.3s ease;
        border: none;
    }

    .stButton>button:hover {
        background-color: #155e75 !important;
        transform: translateY(-2px);
    }

    /* تحسين العناوين */
    h1 {
        color: #004659 !important;
        font-family: 'IBM Plex Sans Arabic', sans-serif;
        padding-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة الحالة (Session State) ---
if "bot_state" not in st.session_state:
    st.session_state["bot_state"] = {
        "smart_mode": False,
        "smart_step": 0,
        "user_profile": {},
        "last_reply": ""
    }

state = st.session_state["bot_state"]


# --- 3. منطق المعالجة (Handle Logic) ---
def process_choice(choice):
    # إذا لم يبدأ الاختبار بعد
    if not state["smart_mode"]:
        state["smart_mode"] = True
        state["smart_step"] = 1
        state["user_profile"] = {}
        return ("🌟 أهلاً بكِ يا مبدعة! راح أساعدج تكتشفين القسم اللي يناسب شغفج بـ 5 خطوات سريعة.\n\n"
                "**السؤال الأول (البيئة):**\n"
                "تحبين شغلج المستقبلي يكون:\n"
                "1️⃣ ورا شاشة وبرمجة وأنظمة ذكية\n"
                "2️⃣ رسم وتخطيط وتصميم معماري\n"
                "3️⃣ حماية معلومات وهكر أخلاقي")

    step = state["smart_step"]
    profile = state["user_profile"]

    # السؤال 1 -> الانتقال لـ 2
    if step == 1:
        profile["base"] = "tech" if choice == "1" else "art" if choice == "2" else "security"
        state["smart_step"] = 2
        return ("**السؤال الثاني (الإبداع):**\n"
                "شنو اللي يشدج أكثر؟\n"
                "1️⃣ بناء برامج ومواقع من الصفر\n"
                "2️⃣ تصميم واجهات تطبيقات موبايل وشكلها النهائي")

    # السؤال 2 -> الانتقال لـ 3
    elif step == 2:
        profile["output"] = "logic" if choice == "1" else "design"
        state["smart_step"] = 3
        return ("**السؤال الثالث (الأسلوب):**\n"
                "تفضلين الدراسة تكون:\n"
                "1️⃣ عملية (مختبرات ومشاريع كود)\n"
                "2️⃣ هندسية (رسم يدوي ومجسمات)")

    # السؤال 3 -> الانتقال لـ 4
    elif step == 3:
        profile["style"] = "practical" if choice == "1" else "engineering"
        state["smart_step"] = 4
        return ("**السؤال الرابع (التحدي):**\n"
                "شنو أصعب تحدي تحبين تواجهينه؟\n"
                "1️⃣ اختراق ثغرات وحماية بيانات\n"
                "2️⃣ بناء ذكاء اصطناعي يفكر مثل الإنسان")

    # السؤال 4 -> الانتقال لـ 5
    elif step == 4:
        profile["challenge"] = "hacking" if choice == "1" else "ai"
        state["smart_step"] = 5
        return ("**السؤال الخامس والأخير (المستقبل):**\n"
                "وين تشوفين نفسج بعد 5 سنوات؟\n"
                "1️⃣ مهندسة برمجيات بموبايل عالمي\n"
                "2️⃣ معمارية تصمم مدن حديثة")

    # السؤال 5 -> النتيجة
    elif step == 5:
        profile["future"] = "apps" if choice == "1" else "cities"
        state["smart_mode"] = False

        # منطق تحديد النتيجة
        if profile.get("base") == "art" or profile.get("future") == "cities":
            res = ["هندسة العمارة اذا كان المعدل اعلى من 69", "هندسة التصميم الرقمي اذا كان المعدل اقل"]
        elif profile.get("base") == "security" or profile.get("challenge") == "hacking":
            res = ["هندسة الأمن السيبراني", "هندسة الحوسبة المتنقلة"]
        elif profile.get("challenge") == "ai":
            res = ["هندسة الذكاء الاصطناعي", "هندسة الحوسبة المتنقلة"]
        else:
            res = ["هندسة الحوسبة المتنقلة", "هندسة التصميم الرقمي"]

        return (f"✨ **تحليل الشخصية اكتمل!**\n\n"
                f"بناءً على اختياراتج، القسم الأنسب لج هو: **{res[0]}**\n"
                f"وممكن أيضاً في: **{res[1]}**\n\n"
                f"مبروك يا مهندسة المستقبل! 🎓")


# --- 4. واجهة العرض ---
st.markdown("<h1 style='text-align:center; color:#ffffff;'>🤖 المساعد الذكي لاختيار القسم</h1>", unsafe_allow_html=True)

# عرض الرسالة الحالية (السؤال)
if not state["last_reply"]:
    state["last_reply"] = process_choice(None)  # تشغيل الترحيب الأول

st.markdown(f"<div class='bot_msg'>{state['last_reply']}</div>", unsafe_allow_html=True)

# عرض أزرار الاختيارات (تختفي عند اكتمال التحليل)
if "مبروك" not in state["last_reply"]:
    cols = st.columns(3)
    with cols[0]:
        if st.button("1️⃣"):
            state["last_reply"] = process_choice("1")
            st.rerun()
    with cols[1]:
        if st.button("2️⃣"):
            state["last_reply"] = process_choice("2")
            st.rerun()
    with cols[2]:
        # يظهر الزر الثالث فقط في السؤال الأول
        if state["smart_step"] == 1:
            if st.button("3️⃣"):
                state["last_reply"] = process_choice("3")
                st.rerun()
else:
    st.balloons()
    if st.button("إعادة الاختبار 🔄"):
        st.session_state["bot_state"] = {"smart_mode": False, "smart_step": 0, "user_profile": {}, "last_reply": ""}
        st.rerun()
if "مبروك" in state["last_reply"]:
    st.balloons()
    # رابط صفحة الـ HTML الرئيسية
    st.markdown("""
        <a href="http://127.0.0.1:8000/ee.html" target="_self" style="text-decoration:none;">
            <div style="text-align:center; padding:10px; background-color:#155e75; color:white; border-radius:10px; margin-top:10px;">
                العودة للصفحة الرئيسية 🏠
            </div>
        </a>
    """, unsafe_allow_html=True)


#  streamlit run smart_mode.py