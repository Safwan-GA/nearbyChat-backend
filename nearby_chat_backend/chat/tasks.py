from firebase.firebase_admin import db, fcm
from datetime import datetime, timezone
from firebase_admin import messaging

def delete_expired_rooms():
    now = datetime.now(timezone.utc)
    rooms = db.collection("rooms").where("expiresAt", "<=", now).stream()

    for room in rooms:
        room_id = room.id

        messages = db.collection("messages").where("roomId", "==", room_id).stream()
        for msg in messages:
            msg.reference.delete()

        room.reference.delete()


def send_expiry_notifications():
    now = datetime.now(timezone.utc)
    warning_time = now.timestamp() + 15 * 60

    rooms = db.collection("rooms").stream()
    for room in rooms:
        data = room.to_dict()
        expires_at = data["expiresAt"].timestamp()

        if now.timestamp() < expires_at <= warning_time:
            token = data.get("creatorToken")
            if token:
                message = messaging.Message(
                    notification=messaging.Notification(
                        title="Room Expiring Soon",
                        body=f"Your room '{data['name']}' will expire soon."
                    ),
                    token=token,
                )
                fcm.send(message)
