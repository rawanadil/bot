"""
صفحات الأستاذ: المحتوى، مراجعة الملخصات، الدرجات (إظهار/إخفاء + Excel)، الحضور، مشاريع التخرج.
"""
from decimal import Decimal, InvalidOperation
from functools import wraps
from io import BytesIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from openpyxl import Workbook

from . import forms as f
from . import models as m
from . import services
from .excel import import_grades


def teacher_required(view):
    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        profile = getattr(request.user, "teacher_profile", None)
        if profile is None:
            return redirect("home")
        request.teacher = profile
        return view(request, *args, **kwargs)
    return wrapper


def own_offering(request, offering_id):
    """الأستاذ يشوف بس المواد اللي هو يدرسها."""
    return get_object_or_404(
        m.CourseOffering.objects.select_related("subject", "academic_year"),
        pk=offering_id, teacher=request.teacher,
    )


def offering_url(offering, tab):
    return f"{reverse('teacher_offering', args=[offering.id])}?tab={tab}"


@teacher_required
def dashboard(request):
    offerings = (
        m.CourseOffering.objects.filter(teacher=request.teacher)
        .select_related("subject", "academic_year")
        .annotate(
            students=Count("enrollments", distinct=True),
            pending=Count("summaries", filter=Q(summaries__status="pending"), distinct=True),
        )
        .order_by("-academic_year__start_date", "subject__name")
    )
    return render(request, "university/teacher/dashboard.html", {
        "offerings": offerings,
        "projects_pending": request.teacher.supervised_projects.filter(status="submitted").count(),
        "notifications": request.user.notifications.filter(is_read=False)[:5],
    })


@teacher_required
def offering_detail(request, offering_id):
    offering = own_offering(request, offering_id)
    tab = request.GET.get("tab", "content")
    ctx = {"offering": offering, "tab": tab}
    if tab == "content":
        ctx["materials"] = offering.materials.all()
        ctx["form"] = f.MaterialForm()
    elif tab == "summaries":
        qs = offering.summaries.select_related("uploaded_by__user").annotate(
            avg_stars=Avg("ratings__stars"), ratings_count=Count("ratings")
        )
        ctx["pending"] = qs.filter(status="pending")
        ctx["approved"] = qs.filter(status="approved")
        ctx["rejected"] = qs.filter(status="rejected")[:20]
        ctx["reject_form"] = f.RejectForm()
    elif tab == "grades":
        ctx["assessments"] = offering.assessments.annotate(n=Count("grades")).order_by("date", "id")
        ctx["form"] = f.AssessmentForm()
    elif tab == "attendance":
        ctx["sessions"] = offering.sessions.annotate(
            present=Count("attendance", filter=Q(attendance__status__in=["present", "late"]))
        )
        ctx["form"] = f.SessionForm(initial={"date": timezone.localdate()})
        ctx["enrolled"] = offering.enrollments.count()
    else:
        raise Http404
    return render(request, "university/teacher/offering.html", ctx)


# ---------------- المحتوى (نظري / عملي) ----------------

@teacher_required
@require_POST
def material_add(request, offering_id):
    offering = own_offering(request, offering_id)
    form = f.MaterialForm(request.POST, request.FILES)
    if form.is_valid():
        form.instance.offering = offering
        form.instance.uploaded_by = request.teacher
        form.save()
        messages.success(request, "انضاف المحتوى.")
    else:
        messages.error(request, " ".join(e for errs in form.errors.values() for e in errs))
    return redirect(offering_url(offering, "content"))


@teacher_required
@require_POST
def material_delete(request, material_id):
    material = get_object_or_404(m.CourseMaterial, pk=material_id, offering__teacher=request.teacher)
    offering = material.offering
    material.delete()
    return redirect(offering_url(offering, "content"))


# ---------------- مراجعة الملخصات ----------------

@teacher_required
@require_POST
def summary_review(request, summary_id, action):
    summary = get_object_or_404(m.Summary, pk=summary_id, offering__teacher=request.teacher)
    student_user = summary.uploaded_by.user
    link = f"/subjects/{summary.offering_id}/?tab=summaries"

    if action == "approve":
        summary.status = m.Summary.Status.APPROVED
        summary.rejection_reason = ""
        services.notify(student_user, "انقبل ملخصك", summary.title, link)
    elif action == "reject":
        form = f.RejectForm(request.POST)
        if not form.is_valid():
            messages.error(request, "اكتب سبب الرفض.")
            return redirect(offering_url(summary.offering, "summaries"))
        summary.status = m.Summary.Status.REJECTED
        summary.is_recommended = False
        summary.rejection_reason = form.cleaned_data["reason"]
        services.notify(student_user, "انرفض ملخصك", f"{summary.title}: {summary.rejection_reason}", link)
    elif action == "recommend":
        if summary.status != m.Summary.Status.APPROVED:
            raise Http404
        summary.is_recommended = not summary.is_recommended
    else:
        raise Http404

    summary.reviewed_by = request.teacher
    summary.reviewed_at = timezone.now()
    summary.save()
    return redirect(offering_url(summary.offering, "summaries"))


# ---------------- الدرجات ----------------

@teacher_required
@require_POST
def assessment_add(request, offering_id):
    offering = own_offering(request, offering_id)
    form = f.AssessmentForm(request.POST)
    if form.is_valid():
        form.instance.offering = offering
        a = form.save()
        return redirect("teacher_assessment", a.id)
    messages.error(request, "تأكد من البيانات.")
    return redirect(offering_url(offering, "grades"))


def own_assessment(request, assessment_id):
    return get_object_or_404(
        m.Assessment.objects.select_related("offering__subject"),
        pk=assessment_id, offering__teacher=request.teacher,
    )


@teacher_required
def assessment_detail(request, assessment_id):
    a = own_assessment(request, assessment_id)
    students = (
        m.StudentProfile.objects.filter(enrollments__offering=a.offering)
        .select_related("user").order_by("user__full_name")
    )
    grades = {g.student_id: g for g in a.grades.all()}

    if request.method == "POST":
        # حفظ الدرجات اللي كتبها الأستاذ بالجدول
        errors = 0
        for s in students:
            raw = request.POST.get(f"score_{s.id}", "").strip()
            if raw == "":
                continue
            try:
                score = Decimal(raw)
            except InvalidOperation:
                errors += 1
                continue
            if score < 0 or score > a.max_score:
                errors += 1
                continue
            m.Grade.objects.update_or_create(assessment=a, student=s, defaults={"score": score})
        if errors:
            messages.error(request, f"{errors} درجة ما انحفظت (مو رقم أو خارج المدى 0 - {a.max_score}).")
        else:
            messages.success(request, "انحفظت الدرجات.")
        return redirect("teacher_assessment", a.id)

    rows = [{"student": s, "grade": grades.get(s.id)} for s in students]
    return render(request, "university/teacher/assessment.html", {
        "a": a, "rows": rows, "upload_form": f.ExcelUploadForm(),
        "imports": a.imports.order_by("-created_at")[:5],
    })


@teacher_required
@require_POST
def assessment_toggle(request, assessment_id):
    """زر إظهار/إخفاء الدرجات."""
    a = own_assessment(request, assessment_id)
    a.is_published = not a.is_published
    a.save(update_fields=["is_published"])
    if a.is_published:
        services.notify_grades_published(a)
        messages.success(request, "الدرجات صارت ظاهرة للطلاب.")
    else:
        messages.success(request, "الدرجات صارت مخفية عن الطلاب.")
    back = request.POST.get("back", "")
    return redirect(back if back.startswith("/") and not back.startswith("//") else reverse("teacher_assessment", args=[a.id]))


@teacher_required
@require_POST
def assessment_import(request, assessment_id):
    a = own_assessment(request, assessment_id)
    form = f.ExcelUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        messages.error(request, "ارفع ملف .xlsx")
        return redirect("teacher_assessment", a.id)
    try:
        log = import_grades(a, form.cleaned_data["file"], request.teacher)
    except Exception:
        messages.error(request, "ما گدرنا نقرا الملف. تأكد إنه ملف Excel سليم.")
        return redirect("teacher_assessment", a.id)
    if log.rows_ok:
        messages.success(request, f"انقرت {log.rows_ok} درجة من {log.rows_total}.")
    if log.rows_failed or (not log.rows_ok and log.error_log):
        messages.error(request, log.error_log.replace("\n", " | "))
    return redirect("teacher_assessment", a.id)


@teacher_required
def assessment_template(request, assessment_id):
    """ينزل ملف Excel جاهز بأرقام الطلاب، الأستاذ يملي الدرجات ويرجع يرفعه."""
    a = own_assessment(request, assessment_id)
    wb = Workbook()
    ws = wb.active
    ws.append(["student_number", "score", "notes", "name"])
    for s in m.StudentProfile.objects.filter(enrollments__offering=a.offering).select_related("user").order_by("user__full_name"):
        ws.append([s.student_number, None, None, s.user.full_name])
    buf = BytesIO()
    wb.save(buf)
    resp = HttpResponse(buf.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    resp["Content-Disposition"] = f'attachment; filename="grades_{a.id}.xlsx"'
    return resp


# ---------------- الحضور ----------------

@teacher_required
@require_POST
def session_add(request, offering_id):
    offering = own_offering(request, offering_id)
    form = f.SessionForm(request.POST)
    if form.is_valid():
        form.instance.offering = offering
        s = form.save()
        return redirect("teacher_session", s.id)
    messages.error(request, " ".join(e for errs in form.errors.values() for e in errs))
    return redirect(offering_url(offering, "attendance"))


@teacher_required
def session_detail(request, session_id):
    session = get_object_or_404(
        m.LectureSession.objects.select_related("offering__subject"),
        pk=session_id, offering__teacher=request.teacher,
    )
    students = (
        m.StudentProfile.objects.filter(enrollments__offering=session.offering)
        .select_related("user").order_by("user__full_name")
    )
    records = {r.student_id: r for r in session.attendance.all()}
    statuses = dict(m.AttendanceRecord.Status.choices)

    if request.method == "POST":
        # تسجيل الحضور يدوياً (لحد ما يجهز قارئ RFID بالمرحلة الثانية)
        for s in students:
            status = request.POST.get(f"status_{s.id}")
            if status not in statuses:
                continue
            rec = records.get(s.id)
            if rec is None:
                m.AttendanceRecord.objects.create(
                    session=session, student=s, status=status, method="manual", scanned_at=timezone.now()
                )
            elif rec.status != status:
                rec.status = status
                rec.save(update_fields=["status"])
        messages.success(request, "انحفظ الحضور.")
        return redirect("teacher_session", session.id)

    rows = [{"student": s, "record": records.get(s.id)} for s in students]
    return render(request, "university/teacher/session.html", {
        "session": session, "rows": rows, "statuses": m.AttendanceRecord.Status.choices,
    })


@teacher_required
@require_POST
def session_report(request, session_id):
    """يسوي ملف Excel للحضور ويرسله لإيميل الأستاذ."""
    session = get_object_or_404(m.LectureSession, pk=session_id, offering__teacher=request.teacher)
    try:
        services.send_attendance_report(session)
        messages.success(request, f"انرسل ملف الحضور على {request.user.email}")
    except Exception:
        messages.error(request, "انسوى الملف بس ما انرسل الإيميل. تأكد من إعدادات الإيميل.")
    return redirect("teacher_session", session.id)


# ---------------- مشاريع التخرج ----------------

@teacher_required
def projects(request):
    items = (
        request.teacher.supervised_projects.select_related("academic_year")
        .prefetch_related("members__student__user", "hardware_items", "images")
        .order_by("-academic_year__start_date", "title")
    )
    return render(request, "university/teacher/projects.html", {"projects": items})


@teacher_required
@require_POST
def project_status(request, project_id, action):
    p = get_object_or_404(m.GraduationProject, pk=project_id, supervisor=request.teacher)
    if action == "approve":
        p.status = m.GraduationProject.Status.APPROVED
        title = "انقبل مشروع التخرج"
    elif action == "return":
        p.status = m.GraduationProject.Status.DRAFT
        title = "المشرف رجّع المشروع للتعديل"
    else:
        raise Http404
    p.save(update_fields=["status"])
    for mem in p.members.select_related("student__user"):
        services.notify(mem.student.user, title, p.title, "/project/")
    return redirect("teacher_projects")
