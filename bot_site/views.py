# نفس مسارات app.py (نسخة Flask) بس بـ Django
import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from boot2 import chatbot_response
from future_engineer_bot import MODEL_ID, SYSTEM_PROMPT, client

# ================== CHAT ==================
state = {}


def chat_page(request):
    return render(request, "chat.html")


@csrf_exempt
@require_POST
def ask_chat(request):
    data = json.loads(request.body)
    user_message = data.get("message")

    reply = chatbot_response(user_message, state)
    return JsonResponse({"reply": reply})


def ee_page(request):
    return render(request, "ee.html")


# ================== PAS ==================
def home(request):
    return render(request, "general_faq2.html")


@csrf_exempt
@require_POST
def ask_pas(request):
    data = json.loads(request.body)
    user_message = data.get("message")
    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=f"{SYSTEM_PROMPT}\n\nسؤال الطالبة: {user_message}"
        )
        return JsonResponse({"reply": response.text})
    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({"reply": "حبيبتي صارت مشكلة صغيرة بالاتصال، حاولي مرة ثانية."})
