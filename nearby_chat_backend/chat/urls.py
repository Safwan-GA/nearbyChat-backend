from django.urls import path
from .rooms import get_accessible_rooms, join_room, create_room
from .messages import send_message, report_message
from .moderation import admin_delete_room, admin_delete_message
from .views import (
    HealthCheckView,
    AccessibleRoomsView,
    JoinRoomView,
    SendMessageView,
    ReportMessageView,
    AdminDeleteRoomView,
    AdminDeleteMessageView,
)

urlpatterns = [
    path("rooms/accessible/", get_accessible_rooms),
    path("rooms/join/", join_room),
    path("rooms/create/", create_room),
    path("messages/send/", send_message),
    path("messages/report/", report_message),
    path("admin/rooms/delete/", admin_delete_room),
    path("admin/messages/delete/", admin_delete_message),
    path("health/", HealthCheckView.as_view()),
]
