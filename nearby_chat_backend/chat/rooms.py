from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from geopy.distance import geodesic
from datetime import datetime, timezone, timedelta
import json
from .auth import verify_firebase_token
from firebase.firebase_admin import db, firestore
import uuid


@csrf_exempt
def create_room(request):
    user, error = verify_firebase_token(request)
    if error:
        return error
    print("=== HEADERS ===")
    for key, value in request.headers.items():
        print(f"{key}: {value}")
    
    # If you specifically want Authorization
    auth_header = request.headers.get("Authorization")
    print("Authorization header:", auth_header)
    body = json.loads(request.body)
    print(body)
    room_id = body.get("roomId", str(uuid.uuid4()))
    room_name = body.get("name", room_id)
    location = {
    "lat": body.get("lat"),
    "lng": body.get("lng")
    }
    radius = body.get("radiusMeters", 100)
    is_private = body.get("isPrivate", False)
    secret_key = body.get("secretKey", "")
    expires_in_minutes = body.get("expiresInMinutes", 60)

    # Check if room already exists
    room_ref = db.collection("rooms").document(room_id)
    if room_ref.get().exists:
        return JsonResponse({"error": "Room already exists"}, status=400)

    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)

    # Create room
    room_ref.set({
        "name": room_name,
        "location": location,
        "radiusMeters": radius,
        "isPrivate": is_private,
        "secretKey": secret_key,
        "creatorId": user["uid"],
        "membersCount": 0,
        "expiresAt": expires_at
    })

    return JsonResponse({"message": "Room created successfully"})


@csrf_exempt
def get_accessible_rooms(request):
    
    user, error = verify_firebase_token(request)
    if error:
        return error

    body = json.loads(request.body)
    user_lat = body["lat"]
    user_lng = body["lng"]

    rooms_ref = db.collection("rooms").stream()
    accessible_rooms = []

    for room in rooms_ref:
        data = room.to_dict()
        expires_at = data["expiresAt"].timestamp()

        if expires_at < datetime.now(timezone.utc).timestamp():
            continue

        room_location = (data["location"]["lat"], data["location"]["lng"])
        user_location = (user_lat, user_lng)
        distance = geodesic(room_location, user_location).meters

        if distance <= data["radiusMeters"]:
            accessible_rooms.append({
                "id": room.id,
                "name": data["name"],
                "isPrivate": data["isPrivate"],
                "membersCount": data.get("membersCount", 0),
                "radiusMeters": data["radiusMeters"],
                "creatorId": data["creatorId"],
                "expiresAt": data["expiresAt"].isoformat(),
            })
    

    return JsonResponse({"rooms": accessible_rooms})


@csrf_exempt
def join_room(request):
    user, error = verify_firebase_token(request)
    if error:
        return error

    body = json.loads(request.body)
    room_id = body["roomId"]
    user_lat = body["lat"]
    user_lng = body["lng"]
    secret_key = body.get("secretKey")

    room_ref = db.collection("rooms").document(room_id)
    room_doc = room_ref.get()

    if not room_doc.exists:
        return JsonResponse({"error": "Room not found"}, status=404)

    data = room_doc.to_dict()

    if data["expiresAt"].timestamp() < datetime.now(timezone.utc).timestamp():
        return JsonResponse({"error": "Room expired"}, status=403)

    room_location = (data["location"]["lat"], data["location"]["lng"])
    user_location = (user_lat, user_lng)
    distance = geodesic(room_location, user_location).meters

    if distance > data["radiusMeters"]:
        return JsonResponse({"error": "Out of range"}, status=403)

    if data["isPrivate"] and secret_key != data["secretKey"]:
        return JsonResponse({"error": "Invalid secret key"}, status=403)

    db.collection("room_members").add({
        "roomId": room_id,
        "userId": user["uid"],
        "joinedAt": datetime.now(timezone.utc),
    })

    room_ref.update({"membersCount": firestore.Increment(1)})

    return JsonResponse({"status": "joined"})
