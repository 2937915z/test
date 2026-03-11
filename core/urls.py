from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),

    path("accounts/register/", views.register_view, name="register"),

    path("courses/", views.courses_view, name="courses"),
    path("assignments/", views.assignments_view, name="assignments"),
    path("plan-focus/", views.plan_focus_view, name="plan_focus"),

    # AJAX endpoints
    path("api/assignments/<int:assignment_id>/status/", views.api_assignment_status, name="api_assignment_status"),
    path("api/attendance/<int:course_id>/", views.api_upsert_attendance, name="api_upsert_attendance"),
    path("api/plan-items/<int:plan_item_id>/toggle/", views.api_toggle_plan_item, name="api_toggle_plan_item"),
    path("api/plan-items/import/", views.api_import_from_assignments, name="api_import_from_assignments"),
    path("api/focus-sessions/create/", views.api_create_focus_session, name="api_create_focus_session"),
]