from __future__ import annotations

from datetime import date
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class Course(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="courses")
    title = models.CharField(max_length=128)
    day_of_week = models.PositiveSmallIntegerField()  # 0=Mon ... 6=Sun
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=128, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(day_of_week__gte=0) & Q(day_of_week__lte=6), name="course_day_of_week_0_6"),
        ]
        ordering = ["day_of_week", "start_time", "title"]

    def __str__(self) -> str:
        return f"{self.title}"


class Assignment(models.Model):
    class Status(models.TextChoices):
        TODO = "TODO", "To Do"
        IN_PROGRESS = "INPR", "In Progress"
        DONE = "DONE", "Done"

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="assignments")
    title = models.CharField(max_length=128)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=4, choices=Status.choices, default=Status.TODO)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["due_date", "title"]

    def __str__(self) -> str:
        return self.title


class AttendanceRecord(models.Model):
    class Status(models.TextChoices):
        PRESENT = "PRES", "Present"
        LATE = "LATE", "Late"
        ABSENT = "ABSN", "Absent"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="attendance_records")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="attendance_records")
    class_date = models.DateField()
    status = models.CharField(max_length=4, choices=Status.choices, default=Status.PRESENT)
    note = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # wireframe：one record per user/course/date
            models.UniqueConstraint(fields=["user", "course", "class_date"], name="uniq_attendance_user_course_date"),
        ]
        ordering = ["-class_date"]

    def clean(self):
        # Prevent unauthorized access: course must belong to user
        if self.course_id and self.user_id and self.course.user_id != self.user_id:
            raise ValidationError("Attendance course must belong to the same user.")

    def __str__(self) -> str:
        return f"{self.user_id} {self.course_id} {self.class_date} {self.status}"


class DailyPlanItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="plan_items")
    plan_date = models.DateField(default=date.today)
    title = models.CharField(max_length=128)
    is_done = models.BooleanField(default=False)

    # Optional: Planned items are associated with courses (in ER, it is referred to as "opt")
    course = models.ForeignKey(Course, null=True, blank=True, on_delete=models.SET_NULL, related_name="plan_items")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["is_done", "created_at"]

    def clean(self):
        if self.course_id and self.course.user_id != self.user_id:
            raise ValidationError("PlanItem course must belong to the same user.")

    def __str__(self) -> str:
        return f"{self.plan_date}: {self.title}"


class FocusSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="focus_sessions")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField()
    note = models.CharField(max_length=255, blank=True)

    # Related object: Assignment or project item (choose either one)
    assignment = models.ForeignKey(Assignment, null=True, blank=True, on_delete=models.SET_NULL, related_name="focus_sessions")
    plan_item = models.ForeignKey(DailyPlanItem, null=True, blank=True, on_delete=models.SET_NULL, related_name="focus_sessions")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(duration_minutes__gt=0), name="focus_duration_gt_0"),
            # XOR: Assignment and plan_item cannot be associated simultaneously.
            models.CheckConstraint(
                check=~(Q(assignment__isnull=False) & Q(plan_item__isnull=False)),
                name="focus_xor_assignment_planitem",
            ),
        ]
        ordering = ["-start_time"]

    def clean(self):
        if self.end_time and self.start_time and self.end_time <= self.start_time:
            raise ValidationError("end_time must be after start_time.")
        # Prevent Overriding: The associated objects must belong to the same user.
        if self.assignment_id and self.assignment.course.user_id != self.user_id:
            raise ValidationError("Assignment must belong to the same user.")
        if self.plan_item_id and self.plan_item.user_id != self.user_id:
            raise ValidationError("Plan item must belong to the same user.")

    def __str__(self) -> str:
        return f"{self.user_id} {self.duration_minutes}min"