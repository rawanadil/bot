"""
صفحات الموقع (الزائر + الطالب).
صفحات الأستاذ موجودة بملف teacher_views.py
"""
from functools import wraps

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Avg, Count, Prefetch, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.http import require_POST

from . import forms as f
from . import models as m
from . import services


# ---------------------------------------------------------------------
# صلاحيات
# ---------------------------------------------------------------------

def student_required(view):
    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        profile = getattr(request.user, "student_profile", None)
        if profile is None:
            return redirect("home")
        request.student = profile
        return view(request, *args, **kwargs)
    return wrapper


def role_home(user):
    if hasattr(user, "teacher_profile"):
        return reverse("teacher_dashboard")
    if hasattr(user, "student_profile"):
        return reverse("dashboard")
    if user.is_staff:
        return reverse("admin:index")
    return reverse("home")


# ---------------------------------------------------------------------
# 1) مرحلة ما قبل التسجيل
# ---------------------------------------------------------------------

def home(request):
    """الصفحة الرئيسية: الشات بوت والأسئلة الشائعة."""
    q = request.GET.get("q", "").strip()
    faqs = m.FAQ.objects.filter(is_active=True)
    if q:
        faqs = faqs.filter(Q(question__icontains=q) | Q(answer__icontains=q))
    else:
        # سؤال واحد من كل تصنيف حتى تتنوع الأسئلة
        seen, picked = set(), []
        for faq in faqs.order_by("intent", "id"):
            if faq.intent not in seen:
                seen.add(faq.intent)
                picked.append(faq)
        faqs = picked
    return render(request, "university/home.html", {
        "faqs": faqs[:12], "q": q, "departments": m.Department.objects.all(),
    })


# ---------------------------------------------------------------------
# 2) التسجيل وتسجيل الدخول
# ---------------------------------------------------------------------

def send_verification_email(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    link = request.build_absolute_uri(reverse("verify_email", args=[uid, token]))
    send_mail(
        "تأكيد الإيميل الجامعي",
        f"أهلاً {user.full_name}\n\nاضغطي على الرابط حتى تأكدين إيميلك:\n{link}",
        None,
        [user.email],
    )


def register(request):
    if request.user.is_authenticated:
        return redirect(role_home(request.user))
    form = f.RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        with transaction.atomic():
            user = m.User.objects.create_user(
                d["email"], d["password1"], full_name=d["full_name"], role=m.User.Role.STUDENT
            )
            photo = d["photo_data"]
            student = m.StudentProfile.objects.create(
                user=user,
                student_number=d["student_number"],
                department=d["department"],
                batch_year=d["batch_year"],
                current_stage=d["current_stage"],
                face_consent=True,
                live_photo_taken_at=timezone.now(),
                face_embedding=services.compute_face_embedding(photo),
            )
            student.live_photo.save(photo.name, photo)
            services.auto_enroll(student)
        login(request, user)
        # بعد login لأن رمز التأكيد يعتمد على وقت آخر دخول
        send_verification_email(request, user)
        messages.success(request, "انسوى حسابك. دزينالك رابط تأكيد على إيميلك الجامعي.")
        return redirect("dashboard")
    return render(request, "university/register.html", {"form": form})


def verify_email(request, uidb64, token):
    try:
        user = m.User.objects.get(pk=urlsafe_base64_decode(uidb64).decode())
    except (m.User.DoesNotExist, ValueError, TypeError):
        user = None
    if user and default_token_generator.check_token(user, token):
        user.is_email_verified = True
        user.save(update_fields=["is_email_verified"])
        messages.success(request, "تأكد إيميلك الجامعي.")
    else:
        messages.error(request, "الرابط غلط أو منتهي.")
    return redirect("home")


@login_required
@require_POST
def resend_verification(request):
    if not request.user.is_email_verified:
        send_verification_email(request, request.user)
        messages.success(request, "دزينا رابط التأكيد مرة ثانية.")
    return redirect(role_home(request.user))


@login_required
def after_login(request):
    return redirect(role_home(request.user))


# ---------------------------------------------------------------------
# 3) داشبورد الطالب
# ---------------------------------------------------------------------

@student_required
def dashboard(request):
    student = request.student
    services.auto_enroll(student)
    year = services.current_year()

    offerings = (
        m.CourseOffering.objects.filter(enrollments__student=student)
        .select_related("subject", "teacher__user", "academic_year")
        .order_by("-academic_year__start_date", "subject__name")
    )
    if year:
        offerings = offerings.filter(academic_year=year)

    # الدرجات الظاهرة بس (is_published = True)
    grades = (
        m.Grade.objects.filter(student=student, assessment__is_published=True, assessment__offering__in=offerings)
        .select_related("assessment__offering__subject")
        .order_by("assessment__offering__subject__name", "assessment__date")
    )
    by_offering = {}
    for g in grades:
        by_offering.setdefault(g.assessment.offering_id, []).append(g)

    cards = []
    for o in offerings:
        cards.append({
            "offering": o,
            "grades": by_offering.get(o.id, []),
            "attendance": services.attendance_summary(student, o),
        })

    # جدول الأنشطة: كل درجة مقسمة حسب النوع
    kinds = dict(m.Assessment.Kind.choices)
    activity = {}
    for g in grades:
        activity.setdefault(kinds[g.assessment.kind], []).append(g)

    return render(request, "university/student/dashboard.html", {
        "student": student,
        "year": year,
        "cards": cards,
        "activity": activity,
        "notifications": request.user.notifications.filter(is_read=False)[:5],
    })


# ---------------------------------------------------------------------
# 4) صفحة المادة: نظري / عملي / ملخصات الطلاب
# ---------------------------------------------------------------------

def get_student_offering(student, offering_id):
    offering = get_object_or_404(
        m.CourseOffering.objects.select_related("subject", "teacher__user", "academic_year"), pk=offering_id
    )
    if not offering.enrollments.filter(student=student).exists():
        raise Http404
    return offering


@student_required
def subject_detail(request, offering_id):
    student = request.student
    offering = get_student_offering(student, offering_id)
    tab = request.GET.get("tab", "theory")
    if tab not in ("theory", "practical", "summaries"):
        tab = "theory"

    ctx = {"offering": offering, "tab": tab, "student": student}
    if tab in ("theory", "practical"):
        ctx["materials"] = offering.materials.filter(section=tab)
    else:
        my_ratings = m.SummaryRating.objects.filter(student=student)
        ctx["summaries"] = (
            m.Summary.objects.visible_to(student)
            .filter(offering__subject=offering.subject, offering__teacher=offering.teacher)
            .select_related("uploaded_by__user", "offering__academic_year")
            .annotate(avg_stars=Avg("ratings__stars"), ratings_count=Count("ratings"))
            .prefetch_related(Prefetch("ratings", queryset=my_ratings, to_attr="my_rating"))
        )
        ctx["my_summaries"] = student.summaries.filter(offering=offering).exclude(status="approved")
        ctx["form"] = f.SummaryForm()
        ctx["attendance"] = services.attendance_summary(student, offering)
    return render(request, "university/student/subject.html", ctx)


@student_required
def summary_upload(request, offering_id):
    offering = get_student_offering(request.student, offering_id)
    form = f.SummaryForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        summary = form.save(commit=False)
        summary.offering = offering
        summary.uploaded_by = request.student
        summary.save()
        services.notify(
            offering.teacher.user, "ملخص جديد بانتظار المراجعة",
            f"{summary.title} - {offering.subject.name}", f"/teacher/offerings/{offering.id}/?tab=summaries",
        )
        messages.success(request, "انرفع الملخص. راح يظهر للطلاب بعد موافقة الأستاذ.")
        return redirect(f"{reverse('subject_detail', args=[offering.id])}?tab=summaries")
    return render(request, "university/student/summary_upload.html", {"form": form, "offering": offering})


@student_required
@require_POST
def summary_rate(request, summary_id):
    student = request.student
    summary = get_object_or_404(m.Summary.objects.visible_to(student), pk=summary_id)
    form = f.RatingForm(request.POST)
    if summary.uploaded_by_id == student.id:
        messages.error(request, "ما تكدرين تقيمين ملخصك.")
    elif form.is_valid():
        m.SummaryRating.objects.update_or_create(
            summary=summary, student=student, defaults={"stars": form.cleaned_data["stars"]}
        )
        messages.success(request, "انحفظ تقييمك.")
    back = request.POST.get("back") or reverse("dashboard")
    return redirect(back if back.startswith("/") and not back.startswith("//") else reverse("dashboard"))


# ---------------------------------------------------------------------
# 5) مشروع التخرج (المرحلة الرابعة بس)
# ---------------------------------------------------------------------

def my_project(student):
    return (
        m.GraduationProject.objects.filter(members__student=student)
        .order_by("-academic_year__start_date").first()
    )


@student_required
def project_edit(request):
    student = request.student
    if not student.is_final_year:
        messages.error(request, "مشروع التخرج بس لطلاب المرحلة الرابعة.")
        return redirect("dashboard")
    project = my_project(student)
    year = services.current_year()
    if project is None and year is None:
        messages.error(request, "ماكو سنة دراسية حالية. راجعي الأدمن.")
        return redirect("dashboard")

    form = f.ProjectForm(request.POST or None, instance=project)
    form.fields["supervisor"].queryset = m.TeacherProfile.objects.filter(department=student.department)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            p = form.save(commit=False)
            if project is None:
                p.academic_year = year
                p.department = student.department
            p.save()
            if project is None:
                m.ProjectMember.objects.create(project=p, student=student, is_leader=True)
        messages.success(request, "انحفظ المشروع.")
        return redirect("project_edit")

    return render(request, "university/student/project.html", {
        "form": form,
        "project": project,
        "member_form": f.MemberAddForm(),
        "hardware_form": f.HardwareForm(),
        "image_form": f.ProjectImageForm(),
    })


def _project_or_404(request):
    project = my_project(request.student)
    if project is None or not request.student.is_final_year:
        raise Http404
    return project


@student_required
@require_POST
def project_add(request, what):
    project = _project_or_404(request)
    if project.status == m.GraduationProject.Status.APPROVED:
        messages.error(request, "المشروع مقبول وما ينعدل.")
        return redirect("project_edit")

    if what == "member":
        form = f.MemberAddForm(request.POST)
        if form.is_valid():
            other = m.StudentProfile.objects.filter(student_number=form.cleaned_data["student_number"]).first()
            if other is None:
                messages.error(request, "ماكو طالب بهذا الرقم.")
            elif other.current_stage != 4:
                messages.error(request, "الطالب مو بالمرحلة الرابعة.")
            elif my_project(other):
                messages.error(request, "الطالب عنده مشروع من قبل.")
            else:
                m.ProjectMember.objects.create(project=project, student=other)
                services.notify(other.user, "انضفت لمشروع تخرج", project.title, "/project/")
    elif what == "hardware":
        form = f.HardwareForm(request.POST)
        if form.is_valid():
            form.instance.project = project
            form.save()
    elif what == "image":
        form = f.ProjectImageForm(request.POST, request.FILES)
        if form.is_valid():
            form.instance.project = project
            form.save()
    else:
        raise Http404
    if not form.is_valid():
        messages.error(request, "تأكدي من البيانات.")
    return redirect("project_edit")


@student_required
@require_POST
def project_remove(request, what, item_id):
    project = _project_or_404(request)
    models_map = {"member": project.members, "hardware": project.hardware_items, "image": project.images}
    if what not in models_map:
        raise Http404
    item = get_object_or_404(models_map[what], pk=item_id)
    if what == "member" and item.is_leader:
        messages.error(request, "ما ينحذف قائد الفريق.")
    else:
        item.delete()
    return redirect("project_edit")


@student_required
@require_POST
def project_submit(request):
    project = _project_or_404(request)
    if project.supervisor is None:
        messages.error(request, "اختاري مشرف قبل الإرسال.")
    elif project.status == m.GraduationProject.Status.DRAFT:
        project.status = m.GraduationProject.Status.SUBMITTED
        project.save(update_fields=["status"])
        services.notify(project.supervisor.user, "مشروع تخرج جديد للمراجعة", project.title, "/teacher/projects/")
        messages.success(request, "انرسل المشروع للمشرف.")
    return redirect("project_edit")


# ---------------------------------------------------------------------
# الإشعارات
# ---------------------------------------------------------------------

@login_required
def notifications(request):
    items = list(request.user.notifications.all()[:50])
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return render(request, "university/notifications.html", {"items": items})
