"""
الفورمات (Forms): كل فورم يمثل استمارة بالموقع، ويتأكد من صحة البيانات قبل الحفظ.
"""
import base64
import uuid
from datetime import date

from django import forms
from django.conf import settings
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm
from django.core.files.base import ContentFile

from . import models as m


class RegisterForm(forms.Form):
    """تسجيل طالب جديد بالإيميل الجامعي + الصورة الحية."""

    full_name = forms.CharField(label="الاسم الكامل", max_length=150)
    email = forms.EmailField(label="الإيميل الجامعي")
    student_number = forms.CharField(label="رقم الطالب", max_length=30)
    department = forms.ModelChoiceField(label="القسم", queryset=m.Department.objects.all())
    current_stage = forms.TypedChoiceField(
        label="المرحلة", choices=m.STAGE_CHOICES, coerce=int, initial=1
    )
    batch_year = forms.IntegerField(
        label="سنة القبول", min_value=2000, max_value=2100, initial=date.today().year
    )
    password1 = forms.CharField(label="كلمة السر", widget=forms.PasswordInput)
    password2 = forms.CharField(label="تأكيد كلمة السر", widget=forms.PasswordInput)
    # الصورة الحية: الكاميرا بالمتصفح تحولها لنص base64 وتحطها بهذا الحقل المخفي
    photo_data = forms.CharField(widget=forms.HiddenInput, error_messages={"required": "لازم تلتقطين صورة حية"})
    face_consent = forms.BooleanField(
        label="أوافق على استخدام صورتي للتحقق من الهوية وقت تسجيل الحضور"
    )

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        domain = settings.UNIVERSITY_EMAIL_DOMAIN
        if domain and not email.endswith("@" + domain):
            raise forms.ValidationError(f"لازم الإيميل يكون جامعي ينتهي بـ @{domain}")
        if m.User.objects.filter(email=email).exists():
            raise forms.ValidationError("هذا الإيميل مسجل من قبل")
        return email

    def clean_student_number(self):
        number = self.cleaned_data["student_number"].strip()
        if m.StudentProfile.objects.filter(student_number=number).exists():
            raise forms.ValidationError("رقم الطالب مسجل من قبل")
        return number

    def clean_photo_data(self):
        data = self.cleaned_data["photo_data"]
        if not data.startswith("data:image/jpeg;base64,"):
            raise forms.ValidationError("الصورة غير صالحة، التقطيها مرة ثانية")
        try:
            raw = base64.b64decode(data.split(",", 1)[1], validate=True)
        except ValueError:
            raise forms.ValidationError("الصورة غير صالحة، التقطيها مرة ثانية")
        if len(raw) > 5 * 1024 * 1024:
            raise forms.ValidationError("الصورة كبيرة")
        return ContentFile(raw, name=f"{uuid.uuid4().hex}.jpg")

    def clean(self):
        data = super().clean()
        p1, p2 = data.get("password1"), data.get("password2")
        if p1 and p2:
            if p1 != p2:
                self.add_error("password2", "كلمتين السر مو متطابقة")
            else:
                try:
                    password_validation.validate_password(p1)
                except forms.ValidationError as e:
                    self.add_error("password1", e)
        return data


class LoginForm(AuthenticationForm):
    username = forms.EmailField(label="الإيميل الجامعي")
    error_messages = {
        "invalid_login": "الإيميل أو كلمة السر غلط",
        "inactive": "الحساب موقوف",
    }


class FileOrUrlMixin:
    """يتأكد إنه اكو ملف أو رابط (مثل القيد اللي بالداتابيس)."""

    def clean(self):
        data = super().clean()
        if not data.get("file") and not data.get("url"):
            raise forms.ValidationError("لازم ترفعين ملف أو تحطين رابط")
        return data


class SummaryForm(FileOrUrlMixin, forms.ModelForm):
    class Meta:
        model = m.Summary
        fields = ["title", "kind", "section", "description", "file", "url"]
        labels = {"section": "نظري أو عملي (اختياري)"}

    def clean(self):
        data = super().clean()
        url = data.get("url") or ""
        if data.get("kind") == m.Summary.Kind.YOUTUBE and not any(
            host in url for host in ("youtube.com/", "youtu.be/")
        ):
            self.add_error("url", "حطي رابط YouTube صحيح")
        if data.get("kind") == m.Summary.Kind.PDF and data.get("file"):
            if not data["file"].name.lower().endswith(".pdf"):
                self.add_error("file", "الملف لازم يكون PDF")
        return data


class RatingForm(forms.Form):
    stars = forms.TypedChoiceField(
        label="التقييم", choices=[(i, i) for i in range(1, 6)], coerce=int
    )


class MaterialForm(FileOrUrlMixin, forms.ModelForm):
    class Meta:
        model = m.CourseMaterial
        fields = ["section", "title", "description", "file", "url"]


class RejectForm(forms.Form):
    reason = forms.CharField(label="سبب الرفض", max_length=500, widget=forms.Textarea(attrs={"rows": 2}))


class AssessmentForm(forms.ModelForm):
    class Meta:
        model = m.Assessment
        fields = ["kind", "title", "max_score", "date"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}


class ExcelUploadForm(forms.Form):
    file = forms.FileField(label="ملف Excel (.xlsx)")

    def clean_file(self):
        f = self.cleaned_data["file"]
        if not f.name.lower().endswith(".xlsx"):
            raise forms.ValidationError("الملف لازم يكون .xlsx")
        return f


class SessionForm(forms.ModelForm):
    class Meta:
        model = m.LectureSession
        fields = ["section", "date", "start_time", "end_time", "room"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
        }

    def clean(self):
        data = super().clean()
        if data.get("start_time") and data.get("end_time") and data["end_time"] <= data["start_time"]:
            self.add_error("end_time", "وقت النهاية لازم يكون بعد البداية")
        return data


class ProjectForm(forms.ModelForm):
    class Meta:
        model = m.GraduationProject
        fields = [
            "title", "supervisor", "features", "objectives", "challenges",
            "conclusion", "future_work", "hardware_description", "external_design_description",
        ]
        widgets = {f: forms.Textarea(attrs={"rows": 3}) for f in fields[2:]}


class MemberAddForm(forms.Form):
    student_number = forms.CharField(label="رقم الطالب", max_length=30)


class HardwareForm(forms.ModelForm):
    class Meta:
        model = m.ProjectHardwareItem
        fields = ["name", "quantity", "notes"]


class ProjectImageForm(forms.ModelForm):
    class Meta:
        model = m.ProjectImage
        fields = ["image", "caption"]
