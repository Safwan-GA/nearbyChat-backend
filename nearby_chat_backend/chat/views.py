from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from firebase_admin import firestore
from firebase.firebase_admin import db, fcm
from geopy.distance import geodesic
from datetime import datetime, timezone
from firebase_admin import messaging
import json

from chat.auth import FirebaseAuthentication


class HealthCheckView(APIView):
    def get(self, request):
        return Response({"status": "ok"})


class AccessibleRoomsView(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_lat = request.data["lat"]
        user_lng = request.data["lng"]

        rooms_ref = db.collection("rooms").stream()
        accessible_rooms = []

        for room in rooms_ref:
            data = room.to_dict()
            expires_at = data["expiresAt"].timestamp()

            if expires_at < datetime.now(timezone.utc).timestamp():
                continue

            room_location = (data["location"]["lat"], data["location"]["lng"])
            user_location = (user_lat, user_lng)
            distance_meters = geodesic(room_location, user_location).meters

            if distance_meters <= data["radiusMeters"]:
                accessible_rooms.append({
                    "id": room.id,
                    "name": data["name"],
                    "isPrivate": data["isPrivate"],
                    "membersCount": data.get("membersCount", 0),
                })

        return Response({"rooms": accessible_rooms})


class JoinRoomView(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_id = request.user["uid"]
        room_id = request.data.get("roomId")
        user_lat = request.data.get("lat")
        user_lng = request.data.get("lng")
        secret_key = request.data.get("secretKey")

        room_ref = db.collection("rooms").document(room_id)
        room_doc = room_ref.get()

        if not room_doc.exists:
            return Response({"error": "Room not found"}, status=404)

        data = room_doc.to_dict()

        if data["expiresAt"].timestamp() < datetime.now(timezone.utc).timestamp():
            return Response({"error": "Room expired"}, status=403)

        room_location = (data["location"]["lat"], data["location"]["lng"])
        user_location = (user_lat, user_lng)
        distance_meters = geodesic(room_location, user_location).meters

        if distance_meters > data["radiusMeters"]:
            return Response({"error": "Out of range"}, status=403)

        if data["isPrivate"] and secret_key != data.get("secretKey"):
            return Response({"error": "Invalid secret key"}, status=403)

        db.collection("room_members").add({
            "roomId": room_id,
            "userId": user_id,
            "joinedAt": datetime.now(timezone.utc),
        })

        room_ref.update({"membersCount": firestore.Increment(1)})

        return Response({"status": "joined"})


class SendMessageView(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_id = request.user["uid"]
        sender_name = request.user.get("name") or request.user.get("email", "Anonymous")

        db.collection("messages").add({
            "roomId": request.data["roomId"],
            "senderId": user_id,
            "senderName": sender_name,
            "content": request.data["content"],
            "createdAt": datetime.now(timezone.utc),
        })

        return Response({"status": "sent"})


class ReportMessageView(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_id = request.user["uid"]

        db.collection("reports").add({
            "roomId": request.data["roomId"],
            "messageId": request.data["messageId"],
            "reportedBy": user_id,
            "reason": request.data["reason"],
            "createdAt": datetime.now(timezone.utc),
        })

        return Response({"status": "reported"})


class AdminDeleteRoomView(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        room_id = request.data["roomId"]

        messages = db.collection("messages").where("roomId", "==", room_id).stream()
        for msg in messages:
            msg.reference.delete()

        members = db.collection("room_members").where("roomId", "==", room_id).stream()
        for m in members:
            m.reference.delete()

        db.collection("rooms").document(room_id).delete()

        return Response({"status": "room deleted"})


class AdminDeleteMessageView(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        message_id = request.data["messageId"]
        db.collection("messages").document(message_id).delete()
        return Response({"status": "message deleted"})
