"""
منطق مشترك تستخدمه الصفحات:
  - تسجيل الطالب تلقائياً بمواد مرحلته
  - حساب بصمة الوجه
  - الإشعارات
  - إرسال ملف الحضور للأستاذ بالإيميل
"""
import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models import Count, Q
from django.utils import timezone

from . import models as m

log = logging.getLogger(__name__)


def current_year():
    return m.AcademicYear.objects.filter(is_current=True).first()


def auto_enroll(student):
    """يسجل الطالب بكل مواد قسمه ومرحلته بالسنة الحالية (إذا مو مسجل)."""
    year = current_year()
    if not year:
        return
    offerings = m.CourseOffering.objects.filter(
        academic_year=year,
        subject__department=student.department,
        subject__stage=student.current_stage,
    ).exclude(enrollments__student=student)
    m.Enrollment.objects.bulk_create(
        [m.Enrollment(student=student, offering=o) for o in offerings], ignore_conflicts=True
    )
    m.StageHistory.objects.get_or_create(
        student=student, academic_year=year, defaults={"stage": student.current_stage}
    )


def compute_face_embedding(image_file):
    """
    يحسب بصمة الوجه (128 رقم) باستخدام مكتبة face_recognition.
    المكتبة اختيارية (تحتاج dlib). إذا مو منصبة، نرجع None والصورة تنحفظ عادي،
    ونكدر نحسب البصمة بعدين بالأمر: python manage.py compute_embeddings
    """
    try:
        import face_recognition
    except ImportError:
        return None
    try:
        image_file.seek(0)
        image = face_recognition.load_image_file(image_file)
        encodings = face_recognition.face_encodings(image)
        return [float(x) for x in encodings[0]] if encodings else None
    except Exception:  # صورة تالفة أو ماكو وجه
        log.exception("face embedding failed")
        return None


def face_distance(a, b):
    """المسافة بين بصمتين. كلما أصغر = أكثر تشابه (أقل من 0.6 = نفس الشخص عادة)."""
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


def notify(user, title, message="", link=""):
    m.Notification.objects.create(user=user, title=title, message=message, link=link)


def notify_grades_published(assessment):
    students = m.StudentProfile.objects.filter(grades__assessment=assessment).select_related("user")
    m.Notification.objects.bulk_create([
        m.Notification(
            user=s.user,
            title=f"نزلت درجات {assessment.title}",
            message=assessment.offering.subject.name,
            link=f"/subjects/{assessment.offering_id}/",
        )
        for s in students
    ])


def attendance_summary(student, offering):
    """عدد مرات الحضور والغياب للطالب بمادة."""
    return m.AttendanceRecord.objects.filter(student=student, session__offering=offering).aggregate(
        present=Count("id", filter=Q(status__in=["present", "late"])),
        absent=Count("id", filter=Q(status="absent")),
        excused=Count("id", filter=Q(status="excused")),
    ) | {"sessions": offering.sessions.count()}


def send_attendance_report(session):
    """يسوي ملف Excel للحضور ويرسله لإيميل أستاذ المادة."""
    from .excel import export_attendance

    report = export_attendance(session)
    teacher = session.offering.teacher.user
    email = EmailMessage(
        subject=f"حضور {session.offering.subject.name} - {session.date}",
        body="مرفق ملف الحضور.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[teacher.email],
    )
    report.open("rb")
    email.attach(report.name.rsplit("/", 1)[-1], report.read(),
                 "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    report.close()
    email.send()
    session.report_sent_at = timezone.now()
    session.save(update_fields=["report_sent_at"])
