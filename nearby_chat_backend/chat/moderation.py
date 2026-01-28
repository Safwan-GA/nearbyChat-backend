from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from firebase.firebase_admin import db
import json
from .auth import verify_firebase_token

@csrf_exempt
def admin_delete_room(request):
    user, error = verify_firebase_token(request)
    if error:
        return error

    body = json.loads(request.body)
    room_id = body["roomId"]

    messages = db.collection("rooms").document(room_id).collection("messages").stream()
    for msg in messages:
        msg.reference.delete()

    members = db.collection("room_members").where("roomId", "==", room_id).stream()
    for m in members:
        m.reference.delete()

    db.collection("rooms").document(room_id).delete()
    return JsonResponse({"status": "room deleted"})


@csrf_exempt
def admin_delete_message(request):
    user, error = verify_firebase_token(request)
    if error:
        return error

    body = json.loads(request.body)
    room_id = body.get("roomId")
    message_id = body.get("messageId")

    if not room_id or not message_id:
        return JsonResponse({"error": "roomId and messageId are required"}, status=400)

    db.collection("rooms").document(room_id) \
        .collection("messages").document(message_id).delete()

    return JsonResponse({"status": "message deleted"})
