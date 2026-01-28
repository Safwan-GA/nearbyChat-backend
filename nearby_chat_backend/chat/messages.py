from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from firebase.firebase_admin import db, firestore
from datetime import datetime, timezone
import json
import uuid
from .auth import verify_firebase_token

@csrf_exempt
def send_message(request):
    user, error = verify_firebase_token(request)
    if error:
        return error

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    room_id = body.get("roomId")
    content = body.get("content")

    if not room_id or not content:
        return JsonResponse({"error": "roomId and content are required"}, status=400)

    sender_id = user.get("uid", "anonymous")
    sender_name = user.get("name") or user.get("email") or "Anonymous"

    message_id = str(uuid.uuid4())

    message_data = {
        "id": message_id,
        "roomId": room_id,
        "senderId": sender_id,
        "senderName": sender_name,
        "content": content,
        "createdAt": firestore.SERVER_TIMESTAMP,  # ✅ FIXED
    }

    db.collection("rooms") \
      .document(room_id) \
      .collection("messages") \
      .document(message_id) \
      .set(message_data)

    return JsonResponse({"status": "sent", "messageId": message_id}, status=200)



@csrf_exempt
def report_message(request):
    user, error = verify_firebase_token(request)
    if error:
        return error

    body = json.loads(request.body)

    db.collection("reports").add({
        "roomId": body["roomId"],
        "messageId": body["messageId"],
        "reportedBy": user["uid"],
        "reason": body["reason"],
        "createdAt": datetime.now(timezone.utc),
    })

    return JsonResponse({"status": "reported"})
