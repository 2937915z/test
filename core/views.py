from __future__ import annotations

import json
from datetime import date, datetime, timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.http import HttpRequest, JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import RegisterForm, CourseForm, AssignmentForm, PlanItemForm
from .models import Course, Assignment, AttendanceRecord, DailyPlanItem, FocusSession


# -------------------------
# Auth / Main Pages
# -------------------------

def register_view(request: HttpRequest):
    """M1: Register user and log in immediately on success."""
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully.")
            return redirect("core:dashboard")
    else:
        form = RegisterForm()
    return render(request, "auth/register.html", {"form": form})



@login_required
def dashboard(request: HttpRequest):
    """
    S1 Dashboard:
    - upcoming assignments
    - weekly focus minutes
    - attendance rate
    """
    today = date.today()

    # Upcoming assignments (未完成 + 未过期)
    upcoming = (
        Assignment.objects.filter(course__user=request.user)
        .exclude(status=Assignment.Status.DONE)
        .filter(due_date__isnull=False, due_date__gte=today)
        .select_related("course")
        .order_by("due_date")[:10]
    )

    # Weekly focus minutes (从本周一开始)
    start_week = today - timedelta(days=today.weekday())
    total_focus = (
        FocusSession.objects.filter(user=request.user, start_time__date__gte=start_week)
        .aggregate(total=Sum("duration_minutes"))
        .get("total")
        or 0
    )

    # Attendance rate（按当前所有考勤记录计算；你也可改为本周/本月）
    attendance_total = AttendanceRecord.objects.filter(user=request.user).count()
    attendance_present = AttendanceRecord.objects.filter(
        user=request.user,
        status=AttendanceRecord.Status.PRESENT,
    ).count()
    attendance_rate = round((attendance_present / attendance_total) * 100, 1) if attendance_total else 0.0

    return render(
        request,
        "dashboard.html",
        {
            "upcoming": upcoming,
            "total_focus": total_focus,
            "attendance_rate": attendance_rate,
            "attendance_total": attendance_total,
        },
    )


@login_required
def courses_view(request: HttpRequest):
    """
    M2 + M3:
    - Left side: Course creation / course cards
    - Right side: Attendance table (one row per class date + dropdown Present/Late/Absent)
    """
    courses = Course.objects.filter(user=request.user)

    # ---- M2: Create Course ----
    if request.method == "POST":
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.user = request.user
            course.save()
            messages.success(request, "Course created.")
            return redirect(f"{request.path}?course={course.id}")
    else:
        form = CourseForm()

    # ---- Selected course ----
    selected_course = None
    selected_course_id = request.GET.get("course")
    if selected_course_id:
        selected_course = get_object_or_404(Course, pk=selected_course_id, user=request.user)
    elif courses.exists():
        selected_course = courses.first()

    # ---- Attendance rows ----
    attendance_rows: list[dict] = []
    if selected_course:
        today = date.today()

        # The most recent class date for this course (based on the day_of_week system)
        delta = (today.weekday() - selected_course.day_of_week) % 7
        recent_class_date = today - timedelta(days=delta)

        # Generate 6 lines: Past 2 times + Most recent time + Next 3 times
        class_dates = [recent_class_date + timedelta(days=7 * i) for i in range(-2, 4)]

        existing_records = AttendanceRecord.objects.filter(
            user=request.user,
            course=selected_course,
            class_date__in=class_dates,
        )
        records_by_date = {r.class_date: r for r in existing_records}

        for idx, d in enumerate(class_dates, start=1):
            record = records_by_date.get(d)
            date_label = f"{d.isoformat()} (Today)" if d == today else d.isoformat()

            attendance_rows.append(
                {
                    "class_date": d,
                    "date_label": date_label,
                    "session_label": f"Scheduled Class {idx}",
                    "status": record.status if record else AttendanceRecord.Status.PRESENT,
                    "attendance_id": record.id if record else None,
                }
            )

    context = {
        "courses": courses,
        "form": form,
        "selected_course": selected_course,
        "attendance_rows": attendance_rows,
        "attendance_status_choices": AttendanceRecord.Status.choices,
    }
    return render(request, "courses/courses.html", context)



@login_required
def assignments_view(request: HttpRequest):
    """
    M4:
    - Upcoming assignments table
    - Add Assignment form (basic create flow)
    """
    today = date.today()
    upcoming = (
        Assignment.objects.filter(course__user=request.user)
        .exclude(status=Assignment.Status.DONE)
        .filter(due_date__isnull=False, due_date__gte=today)
        .select_related("course")
        .order_by("due_date")
    )

    if request.method == "POST":
        form = AssignmentForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Assignment saved.")
            return redirect("core:assignments")
    else:
        form = AssignmentForm(user=request.user)

    return render(
        request,
        "assignments/assignments.html",
        {
            "upcoming": upcoming,
            "form": form,
        },
    )

@login_required
def plan_focus_view(request: HttpRequest):
    """
    M5 + M6:
    - Today's plan list and add plan item
    - Focus timer UI (saving via AJAX endpoint)
    """
    today = date.today()

    plan_items = (
        DailyPlanItem.objects.filter(user=request.user, plan_date=today)
        .select_related("course")
        .order_by("is_done", "created_at")
    )

    # Optional: Provide an assignment-related dropdown for the FocusSession UI
    upcoming_assignments = (
        Assignment.objects.filter(course__user=request.user)
        .exclude(status=Assignment.Status.DONE)
        .order_by("due_date")[:10]
    )

    if request.method == "POST":
        form = PlanItemForm(request.POST, user=request.user)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.save()
            messages.success(request, "Plan item added.")
            return redirect("core:plan_focus")
    else:
        form = PlanItemForm(user=request.user, initial={"plan_date": today})

    return render(
        request,
        "plan_focus/plan_focus.html",
        {
            "plan_items": plan_items,
            "upcoming_assignments": upcoming_assignments,
            "form": form,
        },
    )


# -------------------------
# Helpers
# -------------------------

def _json_body(request: HttpRequest):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return None


def _parse_iso_datetime(value: str) -> datetime:
    """
    Parse ISO datetime string from JS (supports trailing Z).
    """
    if not isinstance(value, str):
        raise ValueError("Datetime value must be a string")
    value = value.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)



# -------------------------
# AJAX APIs (front-end interactivity evidence)
# -------------------------

@require_POST
@login_required
def api_assignment_status(request: HttpRequest, assignment_id: int):
    """
    body: { "status": "TODO|INPR|DONE" }
    """
    data = _json_body(request)
    if data is None or "status" not in data:
        return HttpResponseBadRequest("Invalid JSON body")

    assignment = get_object_or_404(Assignment, pk=assignment_id, course__user=request.user)
    status = data["status"]

    valid_statuses = {choice[0] for choice in Assignment.Status.choices}
    if status not in valid_statuses:
        return HttpResponseBadRequest("Invalid status")

    assignment.status = status
    assignment.save(update_fields=["status", "updated_at"])

    return JsonResponse(
        {
            "ok": True,
            "assignment_id": assignment.id,
            "status": assignment.status,
            "status_label": assignment.get_status_display(),
        }
    )

@require_POST
@login_required
def api_upsert_attendance(request: HttpRequest, course_id: int):
    """
    body:
      {
        "class_date": "YYYY-MM-DD",
        "status": "PRES|LATE|ABSN",
        "note": ""
      }
    """
    data = _json_body(request)
    if data is None:
        return HttpResponseBadRequest("Invalid JSON body")

    course = get_object_or_404(Course, pk=course_id, user=request.user)

    try:
        class_date_value = date.fromisoformat(data.get("class_date"))
    except Exception:
        return HttpResponseBadRequest("Invalid class_date")

    status = data.get("status", AttendanceRecord.Status.PRESENT)
    valid_statuses = {choice[0] for choice in AttendanceRecord.Status.choices}
    if status not in valid_statuses:
        return HttpResponseBadRequest("Invalid status")

    note = (data.get("note") or "").strip()

    record, created = AttendanceRecord.objects.update_or_create(
        user=request.user,
        course=course,
        class_date=class_date_value,
        defaults={"status": status, "note": note},
    )

    return JsonResponse(
        {
            "ok": True,
            "attendance_id": record.id,
            "created": created,
            "status": record.status,
            "status_label": record.get_status_display(),
            "class_date": record.class_date.isoformat(),
        }
    )


@require_POST
@login_required
def api_toggle_plan_item(request: HttpRequest, plan_item_id: int):
    item = get_object_or_404(DailyPlanItem, pk=plan_item_id, user=request.user)
    item.is_done = not item.is_done
    item.save(update_fields=["is_done"])
    return JsonResponse({"ok": True, "plan_item_id": item.id, "is_done": item.is_done})


@require_POST
@login_required
def api_import_from_assignments(request: HttpRequest):
    """
    body:
      { "assignment_ids": [1,2,3] }  # optional; empty imports top upcoming
    """
    data = _json_body(request)
    if data is None:
        return HttpResponseBadRequest("Invalid JSON body")

    today = date.today()
    ids = data.get("assignment_ids") or []

    qs = Assignment.objects.filter(course__user=request.user).exclude(status=Assignment.Status.DONE)
    if ids:
        qs = qs.filter(id__in=ids)
    else:
        qs = qs.filter(due_date__isnull=False, due_date__gte=today).order_by("due_date")[:5]

    created_count = 0
    for assignment in qs:
        DailyPlanItem.objects.create(
            user=request.user,
            plan_date=today,
            title=assignment.title,
            is_done=False,
            course=assignment.course,
        )
        created_count += 1

    return JsonResponse({"ok": True, "created": created_count})


@require_POST
@login_required
def api_create_focus_session(request: HttpRequest):
    """
    body:
      {
        "start_time": "2026-02-24T12:00:00Z",
        "end_time": "2026-02-24T12:25:00Z",
        "duration_minutes": 25,
        "note": "",
        "assignment_id": 123,   # optional
        "plan_item_id": 456     # optional
      }
    """
    data = _json_body(request)
    if data is None:
        return HttpResponseBadRequest("Invalid JSON body")

    try:
        start_time = _parse_iso_datetime(data["start_time"])
        end_time = _parse_iso_datetime(data["end_time"])
        duration_minutes = int(data["duration_minutes"])
    except Exception:
        return HttpResponseBadRequest("Invalid time/duration")

    note = (data.get("note") or "").strip()
    assignment_id = data.get("assignment_id") or None
    plan_item_id = data.get("plan_item_id") or None

    assignment = None
    plan_item = None

    if assignment_id:
        assignment = get_object_or_404(Assignment, pk=assignment_id, course__user=request.user)
    if plan_item_id:
        plan_item = get_object_or_404(DailyPlanItem, pk=plan_item_id, user=request.user)

    session = FocusSession(
        user=request.user,
        start_time=start_time,
        end_time=end_time,
        duration_minutes=duration_minutes,
        note=note,
        assignment=assignment,
        plan_item=plan_item,
    )

    try:
        session.full_clean()  # XOR / end>start / ownership validation
    except ValidationError as e:
        if hasattr(e, "message_dict"):
            return JsonResponse({"ok": False, "errors": e.message_dict}, status=400)
        return JsonResponse({"ok": False, "errors": e.messages}, status=400)

    session.save()
    return JsonResponse({"ok": True, "session_id": session.id})