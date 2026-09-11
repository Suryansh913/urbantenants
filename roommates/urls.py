from django.urls import path

from . import views

app_name = "roommates"

urlpatterns = [
    # Main discovery page
    path("", views.roommate_list, name="roommate-list"),

    # Profile CRUD
    path("create/", views.roommate_create, name="roommate-create"),
    path("edit/", views.roommate_edit, name="roommate-edit"),
    path("my-profile/", views.my_profile, name="my-roommate-profile"),
    path("my-profile/toggle-visibility/", views.roommate_toggle_visibility, name="roommate-toggle-visibility"),
    path("my-profile/delete/", views.roommate_delete, name="roommate-delete"),

    # Connection requests
    path("requests/", views.connection_requests_dashboard, name="roommate-requests"),
    path("requests/<int:pk>/accept/", views.accept_connection_request, name="accept-roommate-request"),
    path("requests/<int:pk>/reject/", views.reject_connection_request, name="reject-roommate-request"),
    path("requests/<int:pk>/cancel/", views.cancel_connection_request, name="cancel-roommate-request"),

    # Paid chat unlock (Cashfree) — put BEFORE the <int:pk>/ detail route below
    path("chat-unlock/create-order/", views.roommate_chat_unlock_create_order, name="roommate-chat-unlock-create-order"),
    path("chat-unlock/verify/", views.roommate_chat_unlock_verify, name="roommate-chat-unlock-verify"),
    path("<int:pk>/chat-unlock/use/", views.roommate_chat_unlock_use, name="roommate-chat-unlock-use"),

    # Per-profile actions
    path("<int:pk>/send-request/", views.send_connection_request, name="send-roommate-request"),
    path("<int:pk>/report/", views.report_profile, name="report-roommate"),
    path("<int:pk>/block/", views.block_user, name="block-roommate"),

    # Detail page — keep LAST since <int:pk>/ is a catch-all under this prefix
    path("<int:pk>/", views.roommate_detail, name="roommate-detail"),
]
