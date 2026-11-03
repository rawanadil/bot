"""
التعامل مع ملفات Excel:
  - import_grades: الأستاذ يرفع ملف درجات، ونقراه ونخزنه بجدول Grade
  - export_attendance: نطلع ملف Excel بحضور محاضرة (حتى ينرسل للأستاذ)

شكل ملف الدرجات المطلوب (أول سطر عناوين):
    student_number | score | notes (اختياري)
"""
from decimal import Decimal, InvalidOperation
from io import BytesIO

from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from openpyxl import Workbook, load_workbook

from .models import AttendanceRecord, ExcelImport, Grade, LectureSession, StudentProfile


def import_grades(assessment, uploaded_file, teacher):
    """يقرا ملف Excel ويخزن الدرجات. يرجع سجل ExcelImport فيه عدد النجاح والفشل."""
    log = ExcelImport.objects.create(assessment=assessment, uploaded_by=teacher, file=uploaded_file)
    log.file.open("rb")
    sheet = load_workbook(log.file, read_only=True, data_only=True).active
    rows = sheet.iter_rows(values_only=True)

    headers = [str(h).strip().lower() if h else "" for h in next(rows, [])]
    try:
        num_col, score_col = headers.index("student_number"), headers.index("score")
    except ValueError:
        log.error_log = "لازم أول سطر بيه عمود student_number وعمود score"
        log.save()
        return log
    notes_col = headers.index("notes") if "notes" in headers else None

    errors = []
    with transaction.atomic():
        for line_no, row in enumerate(rows, start=2):
            if not row or all(v is None for v in row):
                continue
            log.rows_total += 1
            number = str(row[num_col]).strip() if row[num_col] is not None else ""
            try:
                score = Decimal(str(row[score_col]))
            except (InvalidOperation, TypeError):
                errors.append(f"سطر {line_no}: الدرجة مو رقم")
                continue
            if score < 0 or score > assessment.max_score:
                errors.append(f"سطر {line_no}: الدرجة {score} خارج المدى (0 - {assessment.max_score})")
                continue
            student = StudentProfile.objects.filter(student_number=number).first()
            if not student:
                errors.append(f"سطر {line_no}: ماكو طالب بالرقم {number}")
                continue
            notes = str(row[notes_col] or "") if notes_col is not None else ""
            Grade.objects.update_or_create(
                assessment=assessment, student=student,
                defaults={"score": score, "notes": notes[:200], "imported_from": log},
            )
            log.rows_ok += 1

        log.rows_failed = len(errors)
        log.error_log = "\n".join(errors)
        log.save()
    return log


def export_attendance(session: LectureSession):
    """يسوي ملف Excel بحضور المحاضرة (الاسم، الرقم، الحالة، التاريخ والوقت) ويخزنه بالمحاضرة."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Attendance"
    ws.append([f"{session.offering.subject.name} - {session.date}"])
    ws.append(["رقم الطالب", "الاسم", "الحالة", "التاريخ والوقت", "التحقق من الوجه"])

    records = (
        AttendanceRecord.objects.filter(session=session)
        .select_related("student__user")
        .order_by("student__user__full_name")
    )
    for r in records:
        when = timezone.localtime(r.scanned_at).strftime("%Y-%m-%d %H:%M") if r.scanned_at else ""
        face = {True: "نعم", False: "لا", None: "-"}[r.face_verified]
        ws.append([r.student.student_number, r.student.user.full_name, r.get_status_display(), when, face])

    buffer = BytesIO()
    wb.save(buffer)
    session.report_file.save(f"attendance_{session.pk}_{session.date}.xlsx", ContentFile(buffer.getvalue()))
    return session.report_file
