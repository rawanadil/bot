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
