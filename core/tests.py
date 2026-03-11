from __future__ import annotations

from datetime import date, time
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Course, AttendanceRecord, DailyPlanItem, Assignment, FocusSession


class CoreTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u1", password="pass12345", email="u1@test.com")
        self.user2 = User.objects.create_user(username="u2", password="pass12345", email="u2@test.com")

        self.course = Course.objects.create(
            user=self.user, title="Internet Technology", day_of_week=0,
            start_time=time(10, 0), end_time=time(11, 0), location=""
        )

    def test_attendance_unique_constraint(self):
        AttendanceRecord.objects.create(user=self.user, course=self.course, class_date=date.today(), status="PRES")
        with self.assertRaises(Exception):
            AttendanceRecord.objects.create(user=self.user, course=self.course, class_date=date.today(), status="LATE")

    def test_focus_session_xor(self):
        a = Assignment.objects.create(course=self.course, title="A1", due_date=date.today(), status="TODO")
        p = DailyPlanItem.objects.create(user=self.user, plan_date=date.today(), title="P1")
        start = timezone.now()
        end = start + timezone.timedelta(minutes=25)

        s = FocusSession(
            user=self.user,
            start_time=start,
            end_time=end,
            duration_minutes=25,
            assignment=a,
            plan_item=p,  # Also set to trigger XOR
        )
        with self.assertRaises(Exception):
            s.full_clean()

    def test_login_required_redirect(self):
        resp = self.client.get(reverse("core:assignments"))
        self.assertEqual(resp.status_code, 302)  # redirect to login

    def test_ajax_update_assignment_status(self):
        self.client.login(username="u1", password="pass12345")
        a = Assignment.objects.create(course=self.course, title="A1", due_date=date.today(), status="TODO")

        url = reverse("core:api_assignment_status", kwargs={"assignment_id": a.id})
        resp = self.client.post(url, data='{"status":"DONE"}', content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        a.refresh_from_db()
        self.assertEqual(a.status, "DONE")