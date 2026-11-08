"""
يملي الموقع ببيانات تجريبية حتى تعرضين المشروع للدكتور.
التشغيل: python manage.py create_demo_data

الحسابات (كلمة السر لكلها: demo12345):
  أدمن:   admin@uni.edu
  أستاذ:  teacher@uni.edu
  طالبة مرحلة أولى:  student1@uni.edu
  طالبة مرحلة رابعة: student4@uni.edu
"""
from datetime import date, time, timedelta
from decimal import Decimal

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from university import models as m

PASSWORD = "demo12345"


class Command(BaseCommand):
    help = "إنشاء بيانات تجريبية للعرض"

    @transaction.atomic
    def handle(self, *args, **options):
        if m.User.objects.filter(email="teacher@uni.edu").exists():
            self.stdout.write("البيانات التجريبية موجودة من قبل.")
            return
        call_command("load_initial_data")
        dept = m.Department.objects.get(name="هندسة الذكاء الاصطناعي")
        today = date.today()
        start = today.year if today.month >= 9 else today.year - 1
        old_year, _ = m.AcademicYear.objects.get_or_create(
            name=f"{start - 1}-{start}", defaults={"start_date": date(start - 1, 9, 15), "end_date": date(start, 6, 30)}
        )
        m.AcademicYear.objects.update(is_current=False)
        year, _ = m.AcademicYear.objects.update_or_create(
            name=f"{start}-{start + 1}",
            defaults={"start_date": date(start, 9, 15), "end_date": date(start + 1, 6, 30), "is_current": True},
        )

        def user(email, name, role, **extra):
            return m.User.objects.create_user(
                email, PASSWORD, full_name=name, role=role, is_email_verified=True, **extra
            )

        user("admin@uni.edu", "مدير النظام", "admin", is_staff=True, is_superuser=True)
        teacher = m.TeacherProfile.objects.create(
            user=user("teacher@uni.edu", "د. أحمد علي", "teacher"),
            employee_number="T-100", department=dept, academic_title="مدرس",
        )
        teacher2 = m.TeacherProfile.objects.create(
            user=user("teacher2@uni.edu", "د. سارة حسن", "teacher"),
            employee_number="T-101", department=dept, academic_title="أستاذ مساعد",
        )

        def student(n, name, stage, batch, rfid):
            return m.StudentProfile.objects.create(
                user=user(f"student{n}@uni.edu", name, "student"),
                student_number=f"AI{batch}{n:03d}", department=dept,
                current_stage=stage, batch_year=batch, rfid_uid=rfid, face_consent=True,
            )

        s1 = student(1, "زينب كريم", 1, start, "A1B2C3D1")
        s2 = student(2, "مريم جاسم", 1, start, "A1B2C3D2")
        s3 = student(3, "نور الهدى سعد", 1, start, "A1B2C3D3")
        senior = student(5, "فاطمة علي (دفعة سابقة)", 2, start - 1, "A1B2C3D5")
        s4 = student(4, "رواء عادل", 4, start - 3, "A1B2C3D4")
        s6 = student(6, "هبة محمد", 4, start - 3, "A1B2C3D6")

        prog = m.Subject.objects.create(name="البرمجة 1", code="AI101", department=dept, stage=1)
        math = m.Subject.objects.create(name="الرياضيات", code="AI102", department=dept, stage=1, has_practical=False)
        m.Subject.objects.create(name="تعلم الآلة", code="AI401", department=dept, stage=4)

        prog_old = m.CourseOffering.objects.create(subject=prog, teacher=teacher, academic_year=old_year)
        prog_now = m.CourseOffering.objects.create(subject=prog, teacher=teacher, academic_year=year)
        m.CourseOffering.objects.create(subject=math, teacher=teacher2, academic_year=year)
        ml = m.CourseOffering.objects.create(
            subject=m.Subject.objects.get(code="AI401"), teacher=teacher, academic_year=year
        )
        m.Enrollment.objects.create(student=senior, offering=prog_old)

        from university.services import auto_enroll
        for s in (s1, s2, s3, s4, s6):
            auto_enroll(s)

        m.CourseMaterial.objects.create(
            offering=prog_now, section="theory", title="المحاضرة 1: مقدمة في البرمجة",
            description="شنو يعني برنامج وشلون الكمبيوتر يفهمه", url="https://docs.python.org/3/tutorial/",
            uploaded_by=teacher,
        )
        m.CourseMaterial.objects.create(
            offering=prog_now, section="practical", title="المختبر 1: تنصيب Python",
            url="https://www.python.org/downloads/", uploaded_by=teacher,
        )

        # ملخص من الدفعة السابقة (مقبول وموصى به) + ملخص جديد بانتظار المراجعة
        old_sum = m.Summary.objects.create(
            offering=prog_old, uploaded_by=senior, kind="youtube", title="شرح الحلقات (loops) بالعراقي",
            url="https://www.youtube.com/results?search_query=python+loops+شرح+عربي", status="approved",
            is_recommended=True, reviewed_by=teacher,
        )
        m.SummaryRating.objects.create(summary=old_sum, student=s2, stars=5)
        m.SummaryRating.objects.create(summary=old_sum, student=s3, stars=4)
        m.Summary.objects.create(
            offering=prog_now, uploaded_by=s2, kind="link", title="ملخص المتغيرات وأنواع البيانات",
            url="https://www.w3schools.com/python/python_variables.asp",
        )

        quiz = m.Assessment.objects.create(
            offering=prog_now, kind="quiz", title="كوز 1", max_score=Decimal(5), date=today - timedelta(days=7),
            is_published=True,
        )
        monthly = m.Assessment.objects.create(
            offering=prog_now, kind="monthly", title="الشهري الأول", max_score=Decimal(20), date=today - timedelta(days=2),
        )
        for s, q, mo in ((s1, 4, 17), (s2, 5, 19), (s3, 3, 12)):
            m.Grade.objects.create(assessment=quiz, student=s, score=q)
            m.Grade.objects.create(assessment=monthly, student=s, score=mo)

        for i, status3 in enumerate(["present", "absent", "present"]):
            session = m.LectureSession.objects.create(
                offering=prog_now, date=today - timedelta(days=7 * (3 - i)),
                start_time=time(8, 30), end_time=time(10, 0), room="قاعة 3",
            )
            for s, st in ((s1, "present"), (s2, "present"), (s3, status3)):
                m.AttendanceRecord.objects.create(session=session, student=s, status=st, method="manual")

        project = m.GraduationProject.objects.create(
            title="نظام حضور ذكي بالكارت والتعرف على الوجه", academic_year=year, department=dept,
            supervisor=teacher, features="تسجيل الحضور بالكارت\nتحقق بالكاميرا\nتقرير Excel للأستاذ",
            objectives="تقليل وقت تسجيل الحضور ومنع الحضور بالنيابة",
        )
        m.ProjectMember.objects.create(project=project, student=s4, is_leader=True)
        m.ProjectMember.objects.create(project=project, student=s6)
        m.ProjectHardwareItem.objects.create(project=project, name="ESP32", quantity=1)
        m.ProjectHardwareItem.objects.create(project=project, name="RFID RC522", quantity=1)

        self.stdout.write(self.style.SUCCESS(
            "انسوت البيانات التجريبية. كلمة السر لكل الحسابات: " + PASSWORD + "\n"
            "admin@uni.edu / teacher@uni.edu / student1@uni.edu / student4@uni.edu"
        ))
