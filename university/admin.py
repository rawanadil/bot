"""
لوحة التحكم (Django Admin) على الرابط /admin
منها تكدرين تضيفين وتعدلين كل الجداول بدون ما تكتبين واجهات.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Avg
from django.utils import timezone

from . import models as m


@admin.register(m.User)
class UserAdmin(BaseUserAdmin):
    ordering = ["email"]
    list_display = ["email", "full_name", "role", "is_email_verified", "is_active"]
    list_filter = ["role", "is_active", "is_email_verified"]
    search_fields = ["email", "full_name"]
    fieldsets = [
        (None, {"fields": ["email", "password"]}),
        ("المعلومات", {"fields": ["full_name", "role", "is_email_verified"]}),
        ("الصلاحيات", {"fields": ["is_active", "is_staff", "is_superuser", "groups", "user_permissions"]}),
    ]
    add_fieldsets = [
        (None, {"fields": ["email", "full_name", "role", "password1", "password2"]}),
    ]


@admin.register(m.StudentProfile)
class StudentAdmin(admin.ModelAdmin):
    list_display = ["user", "student_number", "department", "batch_year", "current_stage", "rfid_uid"]
    list_filter = ["department", "current_stage", "batch_year"]
    search_fields = ["user__full_name", "student_number", "rfid_uid"]
    readonly_fields = ["face_embedding"]


@admin.register(m.TeacherProfile)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ["user", "employee_number", "department", "academic_title"]
    search_fields = ["user__full_name", "employee_number"]


admin.site.register([m.Department, m.AcademicYear, m.StageHistory, m.Enrollment, m.ProjectMember])


@admin.register(m.Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "department", "stage", "has_practical"]
    list_filter = ["department", "stage"]


@admin.register(m.CourseOffering)
class OfferingAdmin(admin.ModelAdmin):
    list_display = ["subject", "teacher", "academic_year", "semester"]
    list_filter = ["academic_year", "semester"]


@admin.register(m.CourseMaterial)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ["title", "offering", "section", "created_at"]
    list_filter = ["section"]


# ---------- الملخصات: موافقة / رفض / توصية ----------
@admin.register(m.Summary)
class SummaryAdmin(admin.ModelAdmin):
    list_display = ["title", "kind", "offering", "uploaded_by", "status", "is_recommended", "avg_stars"]
    list_filter = ["status", "kind", "is_recommended"]
    actions = ["approve", "reject", "recommend"]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_avg=Avg("ratings__stars"))

    @admin.display(description="متوسط النجوم")
    def avg_stars(self, obj):
        return round(obj._avg, 1) if obj._avg else "-"

    def _reviewer(self, request):
        return getattr(request.user, "teacher_profile", None)

    @admin.action(description="موافقة على الملخصات المحددة")
    def approve(self, request, queryset):
        queryset.update(status="approved", reviewed_by=self._reviewer(request), reviewed_at=timezone.now())

    @admin.action(description="رفض الملخصات المحددة")
    def reject(self, request, queryset):
        queryset.update(
            status="rejected", is_recommended=False,
            reviewed_by=self._reviewer(request), reviewed_at=timezone.now(),
        )

    @admin.action(description="تحديد كمصدر موصى به")
    def recommend(self, request, queryset):
        queryset.filter(status="approved").update(is_recommended=True)


admin.site.register(m.SummaryRating)


# ---------- الدرجات: إظهار / إخفاء ----------
class GradeInline(admin.TabularInline):
    model = m.Grade
    extra = 0
    fields = ["student", "score", "notes"]


@admin.register(m.Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ["title", "kind", "offering", "max_score", "is_published"]
    list_filter = ["kind", "is_published"]
    inlines = [GradeInline]
    actions = ["publish", "hide"]

    @admin.action(description="إظهار الدرجات للطلاب")
    def publish(self, request, queryset):
        queryset.update(is_published=True)

    @admin.action(description="إخفاء الدرجات عن الطلاب")
    def hide(self, request, queryset):
        queryset.update(is_published=False)


@admin.register(m.ExcelImport)
class ExcelImportAdmin(admin.ModelAdmin):
    list_display = ["assessment", "uploaded_by", "rows_total", "rows_ok", "rows_failed", "created_at"]
    readonly_fields = ["rows_total", "rows_ok", "rows_failed", "error_log"]


# ---------- الحضور ----------
class AttendanceInline(admin.TabularInline):
    model = m.AttendanceRecord
    extra = 0
    fields = ["student", "status", "method", "scanned_at", "face_verified", "face_match_score"]


@admin.register(m.LectureSession)
class SessionAdmin(admin.ModelAdmin):
    list_display = ["offering", "section", "date", "start_time", "room"]
    list_filter = ["date", "section"]
    inlines = [AttendanceInline]
    actions = ["export_excel"]

    @admin.action(description="تصدير الحضور لملف Excel")
    def export_excel(self, request, queryset):
        from .excel import export_attendance

        for session in queryset:
            export_attendance(session)
        self.message_user(request, f"انسوى {queryset.count()} ملف حضور")


# ---------- مشاريع التخرج ----------
class MemberInline(admin.TabularInline):
    model = m.ProjectMember
    extra = 1


class ImageInline(admin.TabularInline):
    model = m.ProjectImage
    extra = 1


class HardwareInline(admin.TabularInline):
    model = m.ProjectHardwareItem
    extra = 1


@admin.register(m.GraduationProject)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["title", "academic_year", "department", "supervisor", "status"]
    list_filter = ["status", "academic_year", "department"]
    inlines = [MemberInline, HardwareInline, ImageInline]


# ---------- الشات بوت ----------
@admin.register(m.FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ["question", "intent", "is_active"]
    list_filter = ["intent", "is_active"]
    search_fields = ["question", "answer"]


@admin.register(m.ChatLog)
class ChatLogAdmin(admin.ModelAdmin):
    list_display = ["message", "user", "created_at"]


admin.site.register(m.Notification)
