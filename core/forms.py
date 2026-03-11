from __future__ import annotations

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Course, Assignment, DailyPlanItem


DAY_OF_WEEK_CHOICES = [
    (0, "Monday"),
    (1, "Tuesday"),
    (2, "Wednesday"),
    (3, "Thursday"),
    (4, "Friday"),
    (5, "Saturday"),
    (6, "Sunday"),
]


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    display_name = forms.CharField(max_length=150, required=False)

    class Meta:
        model = User
        fields = ("username", "email", "display_name", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].strip().lower()
        dn = (self.cleaned_data.get("display_name") or "").strip()
        if dn:
            user.first_name = dn
        if commit:
            user.save()
        return user


class CourseForm(forms.ModelForm):
    # Use "choices" to override the display of model fields (the model itself still contains integers)
    day_of_week = forms.ChoiceField(choices=DAY_OF_WEEK_CHOICES)

    class Meta:
        model = Course
        fields = ("title", "day_of_week", "start_time", "end_time", "location")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["title"].widget.attrs["class"] = "form-control"
        self.fields["day_of_week"].widget.attrs["class"] = "form-select"
        self.fields["start_time"].widget = forms.TimeInput(attrs={"class": "form-control", "type": "time"})
        self.fields["end_time"].widget = forms.TimeInput(attrs={"class": "form-control", "type": "time"})
        self.fields["location"].widget.attrs["class"] = "form-control"

    def clean_day_of_week(self):
        # The ChoiceField returns a string, but here it is converted back to an integer.
        return int(self.cleaned_data["day_of_week"])


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ("course", "title", "due_date", "status", "notes")
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "course": forms.Select(attrs={"class": "form-select"}),
            "due_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["course"].queryset = Course.objects.filter(user=user)


class PlanItemForm(forms.ModelForm):
    class Meta:
        model = DailyPlanItem
        fields = ("plan_date", "title", "is_done", "course")
        widgets = {
            "plan_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Add plan item"}),
            "is_done": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "course": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["course"].queryset = Course.objects.filter(user=user)
        self.fields["course"].required = False