import google.generativeai as genai

# حطي الـ Key مالتج هنا
API_KEY = "AIzaSyCBGTfIsmZT_P9epM3MEm0UkkkIbEh8PYg"
genai.configure(api_key=API_KEY)


def find_working_model():
    print("🔍 جاري البحث عن موديل متاح للـ API الخاص بكِ...")
    try:
        # لجلب قائمة الموديلات المتاحة لهذا الـ Key
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]

        if not available_models:
            print("❌ لا توجد موديلات متاحة لهذا المفتاح.")
            return

        print(f"✅ الموديلات المتاحة لكِ هي: {available_models}")

        # تجربة أول موديل في القائمة (غالباً يكون gemini-1.5-flash أو gemini-pro)
        selected_model = available_models[0]
        print(f"⏳ جاري تجربة الموديل: {selected_model}...")

        model = genai.GenerativeModel(selected_model)
        response = model.generate_content("هلو جيميناي، أنت شغال؟")

        print(f"\n🚀 نجح الاتصال! الموديل الشغال هو: {selected_model}")
        print(f"🤖 رد البوت: {response.text}")

    except Exception as e:
        print(f"\n❌ حدث خطأ أثناء الفحص: {e}")


if __name__ == "__main__":
    find_working_model()

# def ask_ai_api(user_query, context_from_csv):
#     model = genai.GenerativeModel('models/gemini-2.5-flash')
#
#     prompt = f"""
#     أنتِ "روان"، المحللة الذكية والمساعدة الإدارية في جامعة الزهراء (ع).
#     مهمتج هي (الاستنباط التحليلي) من الدليل المرفق أدناه حصراً.
#
#     دليل الجامعة (البيانات الخام):
#     {context_from_csv}
#
#     التعليمات الذهبية للذكاء (نظام روان المطور):
#     1. (التنقيب المجهري): ابحثي في كل كلمة وجملة. إذا سألت الطالبة عن (رابط، فيديو، مستمسك، مبلغ، أو موقع) وكان هذا التفصيل مخفياً أو مذكوراً عرضاً بوسط "جواب لموضوع آخر"، استخرجيه بدقة وصيغيه كجواب مباشر. لا تقولي "لا يوجد" إلا بعد فحص كل الحروف.
#     2. (الربط العنقودي): عند المقارنة، اجمعي معلومات (المعدل، القسط، والمستقبل) من أسطر مختلفة بالدليل لتبني جواباً متكاملاً. مثلاً: إذا سألت عن "الأمن"، اجمعي معلومة القسط من سطر والمواد من سطر آخر ليكون الجواب شاملاً.
#     3. (فهم المقاصد العامية): إذا قالت "أخاف"، "أريد شغل"، أو "حايرة"، اربطي بين مشاعرها وبين (نقاط القوة) المذكورة في الأقسام بالدليل لتقديم نصيحة مبنية على الحقائق فقط.
#     4. (فلترة التداخل): إذا وجدتِ معلومات متداخلة (مثل شروط الزي وقواعد القبول)، ميزي بينهما بدقة وأجيبي عن المطلوب فقط بذكاء.
#     5. (اللهجة والأمانة): اللهجة العراقية (عيني، حبيبتي، يا وردة) هي الأساس، مع الالتزام التام بالدليل وعدم اختراع أي معلومة خارجية.
#
#     سؤال الطالبة: {user_query}
#     """
#
# def chatbot_response(user_input, state):
#     cleaned = clean_text(user_input)
#     dept_name = get_department_from_text(user_input)
#
#     # 🔹 تحديث القسم الحالي ومسح الاقتراح القديم
#     if dept_name:
#         if dept_name != state["active_department"]:
#             state["active_department"] = dept_name
#             state["last_suggested_question"] = None
#
#     # إذا وافق المستخدم على السؤال المقترح
#     if state["last_suggested_question"] and any(word in cleaned for word in ["نعم", "اي", "أكيد", "طبعا"]):
#         match = get_close_matches(
#             clean_text(state["last_suggested_question"]),
#             df_training['Clean_Question'],
#             n=1,
#             cutoff=0.6
#         )
#         state["last_suggested_question"] = None
#         if match:
#             return df_training[df_training['Clean_Question'] == match[0]]['Answer'].values[0]
#         else:
#             return "❌ لم أجد إجابة مناسبة لهذا السؤال."
#
#     # ===============================
#     # 🧠 تفعيل الاختيار الذكي
#     # ===============================
#     if any(word in cleaned for word in [
#         "اختيار ذكي", "اختار لي", "ساعدني اختار", "اختار قسم", "اريد اختار قسم",
#         "ساعدني في اختيار القسم", "مساعدة في الاختيار", "شنو القسم المناسب",
#         "شنو اختار", "اقترح قسم", "أريد مساعدة في اختيار القسم", "اقترح لي قسم",
#         "اختيار قسم", "اختر لي قسم"
#     ]):
#         state["smart_mode"] = True
#         state["user_profile"] = {}
#         return ("خلينا نختار أفضل قسمين لك خطوة خطوة 👇\n"
#                 "السؤال الأول:\n"
#                 "تحب أكثر:\n"
#                 "1️⃣ البرمجة والتفكير المنطقي\n"
#                 "2️⃣ التصميم والرسم\n"
#                 "3️⃣ الشبكات والحماية\n"
#                 "4️⃣ الرياضيات والتحليل\n"
#                 "5️⃣ العمارة والبناء\n"
#                 "اكتب الرقم أو الوصف")
#
#     # ===============================
#     # 🧠 مراحل الاختيار الذكي
#     # ===============================
#     if state["smart_mode"]:
#         # السؤال الأول: الاهتمامات
#         if "interest" not in state["user_profile"]:
#             interests_map = {
#                 "1": "programming", "برمجة": "programming",
#                 "2": "design", "تصميم": "design", "رسم": "design",
#                 "3": "security", "شبكات": "security", "حماية": "security",
#                 "4": "math", "رياضيات": "math", "تحليل": "math",
#                 "5": "architecture", "عمارة": "architecture", "بناء": "architecture"
#             }
#             for key, value in interests_map.items():
#                 if key in cleaned:
#                     state["user_profile"]["interest"] = value
#                     break
#
#             if "interest" not in state["user_profile"]:
#                 return "جاوبني: تحب برمجة، تصميم، شبكات، رياضيات، أو عمارة؟"
#
#             return ("السؤال الثاني:\n"
#                     "تفضل الدراسة تكون:\n"
#                     "1️⃣ عملية (تطبيق ومشاريع)\n"
#                     "2️⃣ نظرية (تحليل ودراسة)\n"
#                     "اكتب 1 أو 2")
#
#         # السؤال الثاني: نوع الدراسة
#         elif "study_type" not in state["user_profile"]:
#             if "1" in cleaned or "عملي" in cleaned:
#                 state["user_profile"]["study_type"] = "practical"
#             elif "2" in cleaned or "نظري" in cleaned:
#                 state["user_profile"]["study_type"] = "theoretical"
#             else:
#                 return "جاوبني: تفضل عملي لو نظري؟"
#
#             return ("السؤال الثالث:\n"
#                     "تحب تشتغل مستقبلاً أكثر مع:\n"
#                     "1️⃣ أجهزة وأنظمة\n"
#                     "2️⃣ برامج وتطبيقات\n"
#                     "3️⃣ تصاميم وواجهات\n"
#                     "اكتب الرقم")
#
#         # السؤال الثالث: نوع العمل
#         elif "work_type" not in state["user_profile"]:
#             if "1" in cleaned:
#                 state["user_profile"]["work_type"] = "hardware"
#             elif "2" in cleaned:
#                 state["user_profile"]["work_type"] = "software"
#             elif "3" in cleaned:
#                 state["user_profile"]["work_type"] = "design"
#             else:
#                 return "جاوبني: 1 أجهزة، 2 برامج، 3 تصميم؟"
#
#             state["smart_mode"] = False
#             interest = state["user_profile"]["interest"]
#             work = state["user_profile"]["work_type"]
#             recommendations = []
#
#             if interest == "programming":
#                 if work == "software":
#                     recommendations = ["هندسة الذكاء الاصطناعي", "هندسة الحوسبة المتنقلة"]
#                 else:
#                     recommendations = ["هندسة الحوسبة المتنقلة", "هندسة الأمن السيبراني"]
#             elif interest == "design":
#                 recommendations = ["هندسة التصميم الرقمي", "هندسة العمارة"]
#             elif interest == "security":
#                 recommendations = ["هندسة الأمن السيبراني", "هندسة الحوسبة المتنقلة"]
#             elif interest == "math":
#                 recommendations = ["هندسة الذكاء الاصطناعي", "هندسة الحوسبة المتنقلة"]
#             elif interest == "architecture":
#                 recommendations = ["هندسة العمارة", "هندسة التصميم الرقمي"]
#
#             state["user_profile"]["recommended"] = recommendations
#             return ("أفضل قسمين لك هما 🎓:\n" + " و ".join(recommendations))
#
#    # ===============================
#     # --- القسط ---
#     if any(word in cleaned for word in [ "تكلفه" ,"قسط","تكلفة" ,"تكلفنا", "مبلغ", "مال", "فلوس"]):
#         if not dept_name:
#             return "رجاءً حدّد القسم حتى أحسب لك القسط."
#         info = get_department_info(dept_name)
#         if info is None:
#             return "ما لقيت معلومات عن هذا القسم."
#
#         gpa_match = re.search(r'\d+', cleaned)
#         if gpa_match:
#             gpa = int(gpa_match.group())
#             if gpa >= 85:
#                 suggestion = get_random_suggestion(dept_name, df_training, state)
#                 return f"القسط في {dept_name} هو {info['Fee_Above_85']} 💵{suggestion}"
#             else:
#                 suggestion = get_random_suggestion(dept_name, df_training)
#                 return f"القسط في {dept_name} هو {info['Fee_Below_85']} 💵{suggestion}"
#         else:
#             suggestion = get_random_suggestion(dept_name, df_training, state)
#             return (f"القسط في {dept_name} حسب بيانات الجامعة:\n"
#                     f"إذا معدلك 85 أو أكثر: {info['Fee_Above_85']}\n"
#                     f"إذا معدلك أقل من 85: {info['Fee_Below_85']}"
#                     f"{suggestion}")
#
#     # --- المهارات والمواد ---
#     elif any(word in cleaned for word in [
#         "مهارات", "مواد", "مقررات", "دورات", "المواد الدراسية",
#         "المهارات المطلوبة", "الكورسات", "المقررات الدراسية",
#         "المواد الأساسية", "المواد الاختيارية", "البرامج الدراسية",
#         "الدورات التدريبية"
#     ]):
#         if dept_name:
#             info = get_department_info(dept_name)
#             suggestion = get_random_suggestion(dept_name, df_training, state)
#             return (f"{dept_name}:\nالمهارات والمواد:\n{info['Key_Courses']}" f"{suggestion}")
#         else:
#             return "رجاءً حدّد القسم حتى أعطيك المهارات والمواد."
#
#     # --- مدة الدراسة ---
#     elif any(word in cleaned for word in
#              ["فتره", "مدة", "مده", "سنه", "سنة", "فترة", "مدة الدراسة", "عدد السنوات", "كم سنة", "كم مدتها"]):
#         if dept_name:
#             info = get_department_info(dept_name)
#             suggestion = get_random_suggestion(dept_name, df_training, state)
#             return (f"{dept_name}:\nمدة الدراسة: {info['Study_Duration_Years']}" f"{suggestion}")
#         else:
#             return "رجاءً حدّد القسم حتى أعطيك مدة الدراسة."
#
#     # --- الحد الأدنى للمعدل ---
#     elif any(word in cleaned for word in ["معدل", "الحد الأدنى", "اقل معدل"]):
#         if dept_name:
#             info = get_department_info(dept_name)
#             suggestion = get_random_suggestion(dept_name, df_training, state)
#             return (f"الحد الأدنى لمعدل {dept_name} هو {info['Min_GPA']}" f"{suggestion}")
#         else:
#             return "رجاءً حدّد القسم حتى أعطيك الحد الأدنى للمعدل."
#
#     # --- تعريف القسم ---
#     elif dept_name and any(word in cleaned for word in [
#         "عرف", "تعريف", "شنو هو", "شنو", "معلومات", "انطيني", "اعرف",
#         "شرح", "نبذة", "عن القسم", "ماذا يدرس", "الدور", "أعطني معلومات",
#         "شرح القسم"
#     ]):
#         info = get_department_info(dept_name)
#         if info is None:
#             return "ما لقيت معلومات عن هذا القسم."
#         suggestion = get_random_suggestion(dept_name, df_training, state)
#
#         return (
#             f"📌 قسم {dept_name}:\n\n"
#             f"🔹 نبذة عن القسم:\n{info['Department_Definition']}\n\n"
#             f"🔹 دور الطالب في هذا القسم:\n{info['Student_Role']}\n\n"
#             f"🔹 أمثلة بسيطة على شغله:\n{info['Simple_Example']}\n\n"
#             f"📚 هذا القسم مناسب إذا تحب هذا نوع من العمل وتريد تتخصص بيه مستقبلاً."
#             f"{suggestion}"
#         )
#
#     # ========================================================
#     # 🧠 النظام الهجين المطور (نسخة المعرض النهائية)
#     # ========================================================
#
#     # 1. المرحلة الأولى: زيادة عدد المرشحين من 10 إلى 20 لضمان عدم ضياع أي معلومة
#     user_embedding = embedding_model.encode([user_input], convert_to_numpy=True)
#     cos_similarities = cosine_similarity(user_embedding, question_embeddings)[0]
#     top_k_indices = np.argsort(cos_similarities)[-20:][::-1]  # زدنا العدد لـ 20
#
#     candidates = []
#     for idx in top_k_indices:
#         candidates.append({
#             "answer": df_training.iloc[idx]['Answer'],
#             "question": df_training.iloc[idx]['Question']
#         })
#
#     # 2. المرحلة الثانية: Cross-Encoder (بدون شروط قاسية)
#     pairs = [[user_input, f"سؤال: {c['question']} إجابة: {c['answer']}"] for c in candidates]
#     rerank_scores = reranker.predict(pairs)
#     ranked_indices = np.argsort(rerank_scores)[::-1]
#
#     final_results = []
#     seen_answers = set()
#
#     for i in ranked_indices:
#         score = rerank_scores[i]
#         ans = candidates[i]['answer']
#
#         # فلتر المستمسكات (خليه مرن أكثر)
#         if "يجيب مستمسكاته" in ans:
#             reg_keywords = ["سجل", "تسجيل", "مستمسك", "تقديم", "ملف", "هوية", "جلب", "أوراق", "وثائق"]
#             if not any(kw in cleaned for kw in reg_keywords):
#                 continue
#
#         # --- التعديل الأهم هنا ---
#         # نزلنا الـ score لـ -3.0 (يعني "جيب كل شي اله علاقة لو 1%")
#         if ans not in seen_answers and score > -4.0:
#             final_results.append(ans)
#             seen_answers.add(ans)
#
#     # 3. بناء الجواب عبر Gemini (أذكى مرحلة)
#     if not final_results:
#         # حتى لو ما لقى شي، نطلب من جيميناي يحاول يجاوب من معلوماته العامة عن الجامعة
#         return ask_ai_api(user_input, "المعلومات في الدليل محدودة حالياً.")
#
#     # نجمع أفضل 10 نتائج (سياق ضخم) ليقوم جيميناي بالفلترة البشرية
#     context = "\n".join([f"سجل {i + 1}: {res}" for i, res in enumerate(final_results[:12])])
#     return ask_ai_api(user_input, context)

# الكود اللي يعتمد على جميناي







# def chatbot_response(user_input, state):
#     cleaned = clean_text(user_input)
#     # 1️⃣ القفل الذهبي (يجب أن يكون أول سطر في الدالة)
#     if state.get("last_suggested_question") and any(word in cleaned for word in ["نعم", "اي", "اكيد", "طبعا"]):
#         saved_q = state["last_suggested_question"]
#         state["last_suggested_question"] = None  # نصفر الآن بعد أن استخرجناه
#         # نرسل السؤال المحفوظ كأنه إدخال جديد
#         enhanced_query = f"أجيبي عن هذا السؤال من الدليل: {saved_q}"
#         return chatbot_response(enhanced_query, state)
#
#     # 2️⃣ الآن نستخرج القسم ونحدث الحالة
#     dept_name = get_department_from_text(user_input)
#     if dept_name:
#         # نصفر الاقتراح فقط إذا كان المستخدم سأل سؤالاً جديداً تماماً عن قسم مختلف
#         # وليس عندما يجيب بـ "اي"
#         if dept_name != state.get("active_department"):
#             state["active_department"] = dept_name
#             state["last_suggested_question"] = None
#
#     # 🧠 تفعيل الاختيار الذكي
#     # ===============================
#     if any(word in cleaned for word in [
#         "اختيار ذكي", "اختار لي", "ساعدني اختار", "اختار قسم", "اريد اختار قسم",
#         "ساعدني في اختيار القسم", "مساعدة في الاختيار", "شنو القسم المناسب",
#         "شنو اختار", "اقترح قسم", "أريد مساعدة في اختيار القسم", "اقترح لي قسم",
#         "اختيار قسم", "اختر لي قسم"
#     ]):
#         state["smart_mode"] = True
#         state["user_profile"] = {}
#         return ("خلينا نختار أفضل قسمين لك خطوة خطوة 👇\n"
#                 "السؤال الأول:\n"
#                 "تحب أكثر:\n"
#                 "1️⃣ البرمجة والتفكير المنطقي\n"
#                 "2️⃣ التصميم والرسم\n"
#                 "3️⃣ الشبكات والحماية\n"
#                 "4️⃣ الرياضيات والتحليل\n"
#                 "5️⃣ العمارة والبناء\n"
#                 "اكتب الرقم أو الوصف")
#
#     # ===============================
#     # 🧠 مراحل الاختيار الذكي
#     # ===============================
#     if state["smart_mode"]:
#         # السؤال الأول: الاهتمامات
#         if "interest" not in state["user_profile"]:
#             interests_map = {
#                 "1": "programming", "برمجة": "programming",
#                 "2": "design", "تصميم": "design", "رسم": "design",
#                 "3": "security", "شبكات": "security", "حماية": "security",
#                 "4": "math", "رياضيات": "math", "تحليل": "math",
#                 "5": "architecture", "عمارة": "architecture", "بناء": "architecture"
#             }
#             for key, value in interests_map.items():
#                 if key in cleaned:
#                     state["user_profile"]["interest"] = value
#                     break
#
#             if "interest" not in state["user_profile"]:
#                 return "جاوبني: تحب برمجة، تصميم، شبكات، رياضيات، أو عمارة؟"
#
#             return ("السؤال الثاني:\n"
#                     "تفضل الدراسة تكون:\n"
#                     "1️⃣ عملية (تطبيق ومشاريع)\n"
#                     "2️⃣ نظرية (تحليل ودراسة)\n"
#                     "اكتب 1 أو 2")
#
#         # السؤال الثاني: نوع الدراسة
#         elif "study_type" not in state["user_profile"]:
#             if "1" in cleaned or "عملي" in cleaned:
#                 state["user_profile"]["study_type"] = "practical"
#             elif "2" in cleaned or "نظري" in cleaned:
#                 state["user_profile"]["study_type"] = "theoretical"
#             else:
#                 return "جاوبني: تفضل عملي لو نظري؟"
#
#             return ("السؤال الثالث:\n"
#                     "تحب تشتغل مستقبلاً أكثر مع:\n"
#                     "1️⃣ أجهزة وأنظمة\n"
#                     "2️⃣ برامج وتطبيقات\n"
#                     "3️⃣ تصاميم وواجهات\n"
#                     "اكتب الرقم")
#
#         # السؤال الثالث: نوع العمل
#         elif "work_type" not in state["user_profile"]:
#             if "1" in cleaned:
#                 state["user_profile"]["work_type"] = "hardware"
#             elif "2" in cleaned:
#                 state["user_profile"]["work_type"] = "software"
#             elif "3" in cleaned:
#                 state["user_profile"]["work_type"] = "design"
#             else:
#                 return "جاوبني: 1 أجهزة، 2 برامج، 3 تصميم؟"
#
#             state["smart_mode"] = False
#             interest = state["user_profile"]["interest"]
#             work = state["user_profile"]["work_type"]
#             recommendations = []
#
#             if interest == "programming":
#                 if work == "software":
#                     recommendations = ["هندسة الذكاء الاصطناعي", "هندسة الحوسبة المتنقلة"]
#                 else:
#                     recommendations = ["هندسة الحوسبة المتنقلة", "هندسة الأمن السيبراني"]
#             elif interest == "design":
#                 recommendations = ["هندسة التصميم الرقمي", "هندسة العمارة"]
#             elif interest == "security":
#                 recommendations = ["هندسة الأمن السيبراني", "هندسة الحوسبة المتنقلة"]
#             elif interest == "math":
#                 recommendations = ["هندسة الذكاء الاصطناعي", "هندسة الحوسبة المتنقلة"]
#             elif interest == "architecture":
#                 recommendations = ["هندسة العمارة", "هندسة التصميم الرقمي"]
#
#             state["user_profile"]["recommended"] = recommendations
#             return ("أفضل قسمين لك هما 🎓:\n" + " و ".join(recommendations))
#     # 3️⃣ تجميع المعلومات الثابتة من ملف (departments_utf8_bom.csv)
#     # نحول هذه المعلومات إلى "سياق" يقرأه Gemini بدلاً من إرجاعها مباشرة
#
#     dept_context = ""
#     if dept_name:
#         info = get_department_info(dept_name)
#         if info is not None:
#             dept_context = f"""
#                     )بيانات شاملة لقسم  {dept_name}):
#                     - التعريف: {info.get('Department_Definition', 'غير متوفر')}
#                     - دور الطالب: {info.get('Student_Role', 'غير متوفر')}
#                     - أمثلة على العمل: {info.get('Simple_Example', 'غير متوفر')}
#                     - الحد الأدنى للمعدل: {info.get('Min_GPA', 'غير متوفر')}
#                     - القسط (85 فأكثر): {info.get('Fee_Above_85', 'غير متوفر')}
#                     - القسط (أقل من 85): {info.get('Fee_Below_85', 'غير متوفر')}
#                     - مدة الدراسة: {info.get('Study_Duration_Years', 'غير متوفر')}
#                     - المواد الأساسية: {info.get('Key_Courses', 'غير متوفر')}
#                     - الهوايات المناسبة: {info.get('Suitable_Hobbies', 'غير متوفر')}
#                     - نوع الدراسة: {info.get('Study_Type', 'غير متوفر')}
#                     """
#     # ========================================================
#     # 🧠 النظام الهجين المطور (نسخة المعرض النهائية)
#     # ========================================================
#
#     # 1. المرحلة الأولى: زيادة عدد المرشحين من 10 إلى 20 لضمان عدم ضياع أي معلومة
#     user_embedding = embedding_model.encode([user_input], convert_to_numpy=True)
#     cos_similarities = cosine_similarity(user_embedding, question_embeddings)[0]
#     top_k_indices = np.argsort(cos_similarities)[-20:][::-1]  # زدنا العدد لـ 20
#
#     candidates = []
#     for idx in top_k_indices:
#         candidates.append({
#             "answer": df_training.iloc[idx]['Answer'],
#             "question": df_training.iloc[idx]['Question']
#         })
#
#     # 2. المرحلة الثانية: Cross-Encoder (بدون شروط قاسية)
#     pairs = [[user_input, f"سؤال: {c['question']} إجابة: {c['answer']}"] for c in candidates]
#     rerank_scores = reranker.predict(pairs)
#     ranked_indices = np.argsort(rerank_scores)[::-1]
#
#     final_results = []
#     seen_answers = set()
#
#     for i in ranked_indices:
#         score = rerank_scores[i]
#         ans = candidates[i]['answer']
#
#         # فلتر المستمسكات (خليه مرن أكثر)
#         if "يجيب مستمسكاته" in ans:
#             reg_keywords = ["سجل", "تسجيل", "مستمسك", "تقديم", "ملف", "هوية", "جلب", "أوراق", "وثائق"]
#             if not any(kw in cleaned for kw in reg_keywords):
#                 continue
#
#         # --- التعديل الأهم هنا ---
#         # نزلنا الـ score لـ -3.0 (يعني "جيب كل شي اله علاقة لو 1%")
#         if ans not in seen_answers and score > -4.0:
#             final_results.append(ans)
#             seen_answers.add(ans)
#
#     # 5️⃣ دمج كل المصادر وإرسالها لـ Gemini
#     if not final_results and not dept_context:
#         return ask_ai_api(user_input, "المعلومات محدودة.")
#
#         # ندمج معلومات الأقسام مع نتائج البحث
#     full_context = dept_context + "\n\nأجوبة مقاربة من الدليل:\n" + "\n".join(final_results[:12])
#
#     # الحصول على إجابة Gemini الذكية
#     ai_answer = ask_ai_api(user_input, full_context)
#
#     # 6️⃣ إضافة الاقتراح العشوائي (التفاعل)
#     target_dept = state.get("active_department") if state.get("active_department") else "الهندسة"
#     suggestion = get_random_suggestion(target_dept, df_training, state)
#
#     return f"{ai_answer}{suggestion}"














# def analyze_query(user_input, cleaned):
#     all_depts = get_department_from_text(user_input)
#
#     # خريطة تربط الكلمات المفتاحية بأسماء الأعمدة بدقة
#     column_mapping = {
#         "Department_Definition": ["تعريف", "شنو هو", "شرح", "نبذة", "عن القسم"],
#         "Student_Role": ["دور الطالب", "شسوي", "شنو شغلي", "عمل الطالب"],
#         "Simple_Example": ["مثال", "شغل عملي", "تطبيق"],
#         "Min_GPA": ["معدل", "يقبل", "قبول", "الحد الادنى"],
#         "Fee_Above_85": ["قسط", "تكلفة", "فلوس", "سعر", "مبلغ"],
#         "Study_Duration_Years": ["مدة", "سنة", "سنين", "كم سنة", "فترة"],
#         "Key_Courses": ["مواد", "مهارات", "كورسات", "دراسة", "منهج"],
#         "Suitable_Hobbies": ["هوايات", "مناسب لمنو", "مهارات مطلوبة"],
#         "Study_Type": ["نوع الدراسة", "نظري", "عملي", "طبيعة"]
#     }
#
#     detected_columns = []
#     for col, keywords in column_mapping.items():
#         if any(kw in cleaned for kw in keywords):
#             detected_columns.append(col)
#
#     # معالجة خاصة للقسط لضمان جلب السعرين
#     if "Fee_Above_85" in detected_columns:
#         detected_columns.append("Fee_Below_85")
#
#     return {
#         "all_depts": all_depts,
#         "detected_columns": list(set(detected_columns)),
#         "primary_dept": all_depts[0] if all_depts else None
#     }
# # ============================
# # ⭐ الدالة المصححة
# # ============================
# def chatbot_response(user_input, state):
#     cleaned = clean_text(user_input)
#
#     # 1. تحليل السؤال (الأقسام + الأعمدة المطلوبة)
#     analysis = analyze_query(user_input, cleaned)
#     depts = analysis["all_depts"]
#     cols = analysis["detected_columns"]
#
#     # تحديث القسم النشط
#     if depts:
#         state["active_department"] = depts[0]
#
#     dept_context = ""  # هذا المحرك الذي سيمنع Gemini من الشخبطة
#
#     # 2. استخراج البيانات من الأعمدة (الأولوية القصوى)
#     if depts:
#         responses = []
#         for dept in depts:
#             info = get_department_info(dept)
#             if info is not None:
#                 parts = [f"📌 معلومات قسم {dept}:"]
#
#                 # ربط يدوي للأعمدة لضمان الدقة
#                 if "Department_Definition" in cols or "تعريف" in cleaned:
#                     parts.append(f"🔹 تعريف القسم: {info.get('Department_Definition', 'غير متوفر')}")
#
#                 if "Min_GPA" in cols or "معدل" in cleaned:
#                     parts.append(f"🔹 الحد الأدنى للمعدل: {info.get('Min_GPA', 'غير متوفر')}")
#
#                 if "Fee_Above_85" in cols or "قسط" in cleaned:
#                     parts.append(f"🔹 القسط (85+): {info.get('Fee_Above_85')} | القسط (أقل): {info.get('Fee_Below_85')}")
#
#                 if "Study_Duration_Years" in cols or "سنة" in cleaned:
#                     parts.append(f"🔹 مدة الدراسة: {info.get('Study_Duration_Years', 'غير متوفر')} سنوات")
#
#                 if "Key_Courses" in cols or "مواد" in cleaned:
#                     parts.append(f"🔹 المواد والمهارات: {info.get('Key_Courses', 'غير متوفر')}")
#
#                 responses.append("\n".join(parts))
#                 dept_context += "\n".join(parts) + "\n"
#
#         # إذا كانت الإجابة كاملة من الأعمدة، نرجعها فوراً وننهي "الشخبطة"
#         if len(responses) > 0 and not analysis["is_complex"]:
#             suggestion = get_random_suggestion(depts[0], df_training, state)
#             return "\n\n".join(responses) + suggestion
#     # ========================================================
#     # 🧠 النظام الهجين المطور (نسخة المعرض النهائية)
#     # ========================================================
#
#     # 1. المرحلة الأولى: زيادة عدد المرشحين من 10 إلى 20 لضمان عدم ضياع أي معلومة
#     user_embedding = embedding_model.encode([user_input], convert_to_numpy=True)
#     cos_similarities = cosine_similarity(user_embedding, question_embeddings)[0]
#     top_k_indices = np.argsort(cos_similarities)[-20:][::-1]  # زدنا العدد لـ 20
#
#     candidates = []
#     for idx in top_k_indices:
#         candidates.append({
#             "answer": df_training.iloc[idx]['Answer'],
#             "question": df_training.iloc[idx]['Question']
#         })
#
#     # 2. المرحلة الثانية: Cross-Encoder (بدون شروط قاسية)
#     pairs = [[user_input, f"سؤال: {c['question']} إجابة: {c['answer']}"] for c in candidates]
#     rerank_scores = reranker.predict(pairs)
#     ranked_indices = np.argsort(rerank_scores)[::-1]
#
#     final_results = []
#     seen_answers = set()
#
#     for i in ranked_indices:
#         score = rerank_scores[i]
#         ans = candidates[i]['answer']
#
#         # فلتر المستمسكات (خليه مرن أكثر)
#         if "يجيب مستمسكاته" in ans:
#             reg_keywords = ["سجل", "تسجيل", "مستمسك", "تقديم", "ملف", "هوية", "جلب", "أوراق", "وثائق"]
#             if not any(kw in cleaned for kw in reg_keywords):
#                 continue
#
#         # --- التعديل الأهم هنا ---
#         # نزلنا الـ score لـ -3.0 (يعني "جيب كل شي اله علاقة لو 1%")
#         if ans not in seen_answers and score > -4.0:
#             final_results.append(ans)
#             seen_answers.add(ans)
#
#     # 5️⃣ دمج كل المصادر وإرسالها لـ Gemini
#     if not final_results and not dept_context:
#         return ask_ai_api(user_input, "المعلومات محدودة.")
#
#         # ندمج معلومات الأقسام مع نتائج البحث
#     full_context = dept_context + "\n\nأجوبة مقاربة من الدليل:\n" + "\n".join(final_results[:12])
#
#     # الحصول على إجابة Gemini الذكية
#     ai_answer = ask_ai_api(user_input, full_context)
#
#     # 6️⃣ إضافة الاقتراح العشوائي (التفاعل)
#     target_dept = state.get("active_department") or "الأقسام"
#     return f"{ai_answer}{get_random_suggestion(target_dept, df_training, state)}"

genai.configure(api_key="AIzaSyCBGTfIsmZT_P9epM3MEm0UkkkIbEh8PYg")