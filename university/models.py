"""
جداول قاعدة البيانات (PostgreSQL) لنظام الجامعة.

كل class هنا = جدول بالداتابيس، وكل حقل = عمود.
Django يحوّلها لجداول SQL عن طريق: python manage.py migrate

الأقسام:
  1) المستخدمين: User + StudentProfile + TeacherProfile
  2) الهيكل الدراسي: Department, AcademicYear, Subject, CourseOffering, Enrollment
  3) محتوى المادة: CourseMaterial (نظري / عملي)
  4) ملخصات الطلاب: Summary + SummaryRating
  5) الدرجات: Assessment + Grade + ExcelImport
  6) الحضور: LectureSession + AttendanceRecord
  7) مشاريع التخرج: GraduationProject + ProjectMember + ProjectImage + ProjectHardwareItem
  8) الشات بوت والإشعارات: FAQ + ChatLog + Notification

(الـ ESP32 والحساسات مرحلة ثانية، ما مضافة هنا)
"""
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.postgres.fields import ArrayField  # noqa: F401  (مستخدم بالمايغريشن القديمة)
from pgvector.django import HnswIndex, VectorField

# أبعاد المتجهات (لازم تطابق الموديل اللي يطلعها)
FACE_DIM = 128   # face_recognition / dlib
TEXT_DIM = 768   # intfloat/multilingual-e5-base
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q


# =====================================================================
# 1) المستخدمين
# =====================================================================

class UserManager(BaseUserManager):
    """يخلي تسجيل الدخول بالإيميل بدل اسم المستخدم."""

    use_in_migrations = True

    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("الإيميل مطلوب")
        user = self.model(email=self.normalize_email(email).lower(), **extra)
        user.set_password(password)  # تتخزن مشفرة (hash) مو نص عادي
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("role", User.Role.ADMIN)
        return self.create_user(email, password, **extra)


class User(AbstractUser):
    """
    جدول واحد لكل المستخدمين (طالب، أستاذ، أدمن).
    المعلومات الخاصة بكل نوع تنحفظ بجدول منفصل (StudentProfile / TeacherProfile).
    """

    class Role(models.TextChoices):
        STUDENT = "student", "طالب"
        TEACHER = "teacher", "أستاذ"
        ADMIN = "admin", "أدمن"

    username = None  # ما نحتاجه، الدخول بالإيميل
    email = models.EmailField("الإيميل الجامعي", unique=True)
    full_name = models.CharField("الاسم الكامل", max_length=150)
    role = models.CharField("الدور", max_length=10, choices=Role.choices, default=Role.STUDENT)
    is_email_verified = models.BooleanField("الإيميل متأكد منه", default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    objects = UserManager()

    class Meta:
        verbose_name = "مستخدم"
        verbose_name_plural = "المستخدمين"

    def __str__(self):
        return f"{self.full_name} <{self.email}>"


class Department(models.Model):
    """الأقسام: ذكاء اصطناعي، أمن سيبراني، ..."""

    name = models.CharField("اسم القسم", max_length=100, unique=True)
    code = models.CharField("رمز القسم", max_length=20, unique=True, blank=True, null=True)

    class Meta:
        verbose_name = "قسم"
        verbose_name_plural = "الأقسام"

    def __str__(self):
        return self.name


class AcademicYear(models.Model):
    """السنة الدراسية مثل 2025-2026. كل شي (مواد، درجات، حضور) يرتبط بيها."""

    name = models.CharField("السنة", max_length=20, unique=True)  # "2025-2026"
    start_date = models.DateField("تاريخ البداية")
    end_date = models.DateField("تاريخ النهاية")
    is_current = models.BooleanField("السنة الحالية", default=False)

    class Meta:
        verbose_name = "سنة دراسية"
        verbose_name_plural = "السنوات الدراسية"
        ordering = ["-start_date"]
        constraints = [
            # بس سنة وحدة تكدر تكون "الحالية"
            models.UniqueConstraint(
                fields=["is_current"], condition=Q(is_current=True), name="only_one_current_year"
            ),
        ]

    def __str__(self):
        return self.name


STAGE_CHOICES = [(1, "المرحلة الأولى"), (2, "المرحلة الثانية"), (3, "المرحلة الثالثة"), (4, "المرحلة الرابعة")]


class StudentProfile(models.Model):
    """معلومات الطالب الإضافية."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    student_number = models.CharField("رقم الطالب", max_length=30, unique=True)
    rfid_uid = models.CharField(
        "رقم كارت RFID", max_length=50, unique=True, blank=True, null=True,
        help_text="الرقم المخزون بالبطاقة الجامعية، يستخدم لتسجيل الحضور",
    )
    department = models.ForeignKey(Department, on_delete=models.PROTECT, verbose_name="القسم")
    batch_year = models.PositiveSmallIntegerField(
        "سنة القبول (الدفعة)", help_text="مثلاً 2025. نحتاجها لشرط مشاركة الملخصات بين الدفعات"
    )
    current_stage = models.PositiveSmallIntegerField("المرحلة الحالية", choices=STAGE_CHOICES, default=1)

    # الصورة الحية اللي تنلتقط وقت التسجيل (من الكاميرا مباشرة)
    live_photo = models.ImageField("الصورة الحية", upload_to="students/live_photos/", blank=True, null=True)
    live_photo_taken_at = models.DateTimeField("وقت التقاط الصورة", blank=True, null=True)
    # بصمة الوجه: أرقام تطلعها مكتبة التعرف على الوجه (مثل face_recognition = 128 رقم)
    # نقارن بيها وقت الحضور بدل ما نقارن الصور نفسها
    # نخزنها بنوع vector مال pgvector حتى نكدر نبحث بالداتابيس عن أقرب وجه بسرعة
    face_embedding = VectorField(dimensions=FACE_DIM, blank=True, null=True, verbose_name="بصمة الوجه")
    face_consent = models.BooleanField("موافقة على استخدام صورة الوجه", default=False)

    class Meta:
        verbose_name = "طالب"
        verbose_name_plural = "الطلاب"
        indexes = [
            # face_recognition يقارن بالمسافة الإقليدية (L2)
            HnswIndex(name="student_face_hnsw", fields=["face_embedding"],
                      m=16, ef_construction=64, opclasses=["vector_l2_ops"]),
        ]

    def __str__(self):
        return f"{self.user.full_name} ({self.student_number})"

    @property
    def is_final_year(self):
        """المرحلة الرابعة = تظهر له خانة مشروع التخرج."""
        return self.current_stage == 4


class StageHistory(models.Model):
    """سجل ترقية الطالب من مرحلة لمرحلة (حتى نعرف بأي سنة كان بأي مرحلة)."""

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="stage_history")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT)
    stage = models.PositiveSmallIntegerField(choices=STAGE_CHOICES)

    class Meta:
        verbose_name = "سجل مرحلة"
        verbose_name_plural = "سجل المراحل"
        constraints = [
            models.UniqueConstraint(fields=["student", "academic_year"], name="one_stage_per_year"),
        ]


class TeacherProfile(models.Model):
    """معلومات الأستاذ الإضافية."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="teacher_profile")
    employee_number = models.CharField("الرقم الوظيفي", max_length=30, unique=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, verbose_name="القسم")
    academic_title = models.CharField("اللقب العلمي", max_length=50, blank=True)  # مدرس، أستاذ مساعد...
    photo = models.ImageField("الصورة", upload_to="teachers/photos/", blank=True, null=True)

    class Meta:
        verbose_name = "أستاذ"
        verbose_name_plural = "الأساتذة"

    def __str__(self):
        return self.user.full_name


# =====================================================================
# 2) الهيكل الدراسي
# =====================================================================

class Subject(models.Model):
    """المادة نفسها (مثلاً: برمجة 1) بغض النظر عن منو يدرسها."""

    name = models.CharField("اسم المادة", max_length=150)
    code = models.CharField("رمز المادة", max_length=30, unique=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="subjects")
    stage = models.PositiveSmallIntegerField("المرحلة", choices=STAGE_CHOICES)
    has_practical = models.BooleanField("بيها عملي", default=True)

    class Meta:
        verbose_name = "مادة"
        verbose_name_plural = "المواد"

    def __str__(self):
        return f"{self.name} ({self.code})"


class CourseOffering(models.Model):
    """
    أهم جدول: يربط المادة + الأستاذ + السنة الدراسية + الفصل.
    مثال: "برمجة 1" يدرسها "د. أحمد" بسنة 2025-2026 الفصل الأول.
    الدرجات والحضور والمحتوى والملخصات كلها مربوطة بهذا الجدول.
    """

    class Semester(models.IntegerChoices):
        FIRST = 1, "الفصل الأول"
        SECOND = 2, "الفصل الثاني"
        FULL_YEAR = 0, "سنوي"

    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="offerings")
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.PROTECT, related_name="offerings")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name="offerings")
    semester = models.PositiveSmallIntegerField("الفصل", choices=Semester.choices, default=Semester.FIRST)

    class Meta:
        verbose_name = "تدريس مادة"
        verbose_name_plural = "تدريس المواد"
        constraints = [
            models.UniqueConstraint(
                fields=["subject", "teacher", "academic_year", "semester"], name="unique_offering"
            ),
        ]

    def __str__(self):
        return f"{self.subject.name} - {self.teacher} - {self.academic_year}"


class Enrollment(models.Model):
    """منو الطالب المسجل بأي مادة."""

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="enrollments")
    offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, related_name="enrollments")
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "تسجيل بمادة"
        verbose_name_plural = "تسجيل الطلاب بالمواد"
        constraints = [
            models.UniqueConstraint(fields=["student", "offering"], name="unique_enrollment"),
        ]


# =====================================================================
# 3) محتوى المادة (الأستاذ يرفعه)
# =====================================================================

class Section(models.TextChoices):
    THEORY = "theory", "نظري"
    PRACTICAL = "practical", "عملي"


def file_or_url_required():
    """قيد بالداتابيس: لازم يكون اكو ملف أو رابط (مو الاثنين فارغين)."""
    return ~(Q(file="") & (Q(url="") | Q(url__isnull=True)))


class CourseMaterial(models.Model):
    """ملفات وروابط الأستاذ داخل خانة النظري أو العملي."""

    offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, related_name="materials")
    section = models.CharField("الخانة", max_length=10, choices=Section.choices)
    title = models.CharField("العنوان", max_length=200)
    description = models.TextField("الوصف", blank=True)
    file = models.FileField("ملف", upload_to="materials/", blank=True)
    url = models.URLField("رابط", blank=True)
    uploaded_by = models.ForeignKey(TeacherProfile, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "محتوى مادة"
        verbose_name_plural = "محتوى المواد"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(condition=file_or_url_required(), name="material_needs_file_or_url"),
        ]

    def __str__(self):
        return self.title


# =====================================================================
# 4) ملخصات الطلاب
# =====================================================================

class SummaryQuerySet(models.QuerySet):
    def visible_to(self, student: StudentProfile):
        """
        شرط ظهور الملخص للطالب:
          - الملخص مقبول من الأستاذ
          - نفس المادة ونفس الأستاذ لمادة مسجل بيها الطالب
          - رافعه من نفس دفعة الطالب أو دفعة أقدم (يعني الدفعات اللاحقة تستفاد)
        """
        offerings = CourseOffering.objects.filter(enrollments__student=student)
        pairs = Q(pk__in=[])
        for subject_id, teacher_id in offerings.values_list("subject_id", "teacher_id"):
            pairs |= Q(offering__subject_id=subject_id, offering__teacher_id=teacher_id)
        return self.filter(
            pairs,
            status=Summary.Status.APPROVED,
            uploaded_by__batch_year__lte=student.batch_year,
        )


class Summary(models.Model):
    """ملخص يرفعه الطالب، والأستاذ يوافق عليه أو يرفضه."""

    class Kind(models.TextChoices):
        PAPER = "paper", "ملخص ورقي (صور)"
        PDF = "pdf", "ملف PDF"
        YOUTUBE = "youtube", "فيديو YouTube"
        LINK = "link", "رابط"
        OTHER = "other", "مصدر آخر"

    class Status(models.TextChoices):
        PENDING = "pending", "بانتظار المراجعة"
        APPROVED = "approved", "مقبول"
        REJECTED = "rejected", "مرفوض"

    # المادة اللي انرفع بيها الملخص (منها نعرف المادة + الأستاذ + السنة)
    offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, related_name="summaries")
    uploaded_by = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="summaries")
    section = models.CharField("الخانة", max_length=10, choices=Section.choices, blank=True)
    kind = models.CharField("النوع", max_length=10, choices=Kind.choices)
    title = models.CharField("العنوان", max_length=200)
    description = models.TextField("الوصف", blank=True)
    file = models.FileField("ملف", upload_to="summaries/", blank=True)
    url = models.URLField("رابط", blank=True)

    # المراجعة من الأستاذ
    status = models.CharField("الحالة", max_length=10, choices=Status.choices, default=Status.PENDING)
    reviewed_by = models.ForeignKey(
        TeacherProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_summaries"
    )
    reviewed_at = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.TextField("سبب الرفض", blank=True)
    is_recommended = models.BooleanField("موصى به من الأستاذ", default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = SummaryQuerySet.as_manager()

    class Meta:
        verbose_name = "ملخص"
        verbose_name_plural = "ملخصات الطلاب"
        ordering = ["-is_recommended", "-created_at"]
        constraints = [
            models.CheckConstraint(condition=file_or_url_required(), name="summary_needs_file_or_url"),
            # ما يصير "موصى به" إلا إذا كان مقبول
            models.CheckConstraint(
                condition=Q(is_recommended=False) | Q(status="approved"), name="recommended_must_be_approved"
            ),
        ]
        indexes = [models.Index(fields=["status"])]

    def __str__(self):
        return self.title


class SummaryRating(models.Model):
    """تقييم بالنجوم (1 إلى 5). كل طالب يقيّم الملخص مرة وحدة بس."""

    summary = models.ForeignKey(Summary, on_delete=models.CASCADE, related_name="ratings")
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="ratings")
    stars = models.PositiveSmallIntegerField("النجوم", validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.CharField("تعليق", max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "تقييم ملخص"
        verbose_name_plural = "تقييمات الملخصات"
        constraints = [
            models.UniqueConstraint(fields=["summary", "student"], name="one_rating_per_student"),
            models.CheckConstraint(condition=Q(stars__gte=1, stars__lte=5), name="stars_between_1_and_5"),
        ]


# =====================================================================
# 5) الدرجات
# =====================================================================

class Assessment(models.Model):
    """
    أي شي عليه درجة: كوز، امتحان شهري، عملي، حضور، ...
    حقل is_published = خاصية إظهار/إخفاء الدرجات، يتحكم بيها الأستاذ.
    """

    class Kind(models.TextChoices):
        QUIZ = "quiz", "كوز"
        MONTHLY = "monthly", "امتحان شهري"
        MIDTERM = "midterm", "نصف السنة"
        FINAL = "final", "امتحان نهائي"
        PRACTICAL = "practical", "عملي"
        ATTENDANCE = "attendance", "درجة الحضور"
        ASSIGNMENT = "assignment", "واجب / تقرير"
        OTHER = "other", "أخرى"

    offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, related_name="assessments")
    kind = models.CharField("النوع", max_length=12, choices=Kind.choices)
    title = models.CharField("العنوان", max_length=150)  # مثلاً "الشهري الأول"
    max_score = models.DecimalField("الدرجة القصوى", max_digits=6, decimal_places=2)
    date = models.DateField("التاريخ", blank=True, null=True)
    is_published = models.BooleanField("الدرجات ظاهرة للطلاب", default=False)

    class Meta:
        verbose_name = "تقييم دراسي"
        verbose_name_plural = "التقييمات الدراسية"
        constraints = [
            models.CheckConstraint(condition=Q(max_score__gt=0), name="max_score_positive"),
        ]

    def __str__(self):
        return f"{self.title} - {self.offering.subject.name}"


class Grade(models.Model):
    """درجة طالب بتقييم معين."""

    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name="grades")
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="grades")
    score = models.DecimalField("الدرجة", max_digits=6, decimal_places=2)
    notes = models.CharField("ملاحظات", max_length=200, blank=True)
    imported_from = models.ForeignKey(
        "ExcelImport", on_delete=models.SET_NULL, null=True, blank=True, related_name="grades"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "درجة"
        verbose_name_plural = "الدرجات"
        constraints = [
            models.UniqueConstraint(fields=["assessment", "student"], name="one_grade_per_assessment"),
            models.CheckConstraint(condition=Q(score__gte=0), name="score_not_negative"),
        ]

    def clean(self):
        if self.score is not None and self.score > self.assessment.max_score:
            raise ValidationError({"score": "الدرجة أكبر من الدرجة القصوى"})


class ExcelImport(models.Model):
    """سجل كل ملف Excel رفعه الأستاذ (درجات)، وكم سطر نجح وكم فشل."""

    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name="imports")
    uploaded_by = models.ForeignKey(TeacherProfile, on_delete=models.PROTECT)
    file = models.FileField("ملف Excel", upload_to="imports/grades/")
    rows_total = models.PositiveIntegerField(default=0)
    rows_ok = models.PositiveIntegerField(default=0)
    rows_failed = models.PositiveIntegerField(default=0)
    error_log = models.TextField("الأخطاء", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "استيراد Excel"
        verbose_name_plural = "سجل استيراد Excel"


# =====================================================================
# 6) الحضور
# =====================================================================

class LectureSession(models.Model):
    """محاضرة وحدة بتاريخ ووقت معين. الحضور ينسجل عليها."""

    offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, related_name="sessions")
    section = models.CharField("نظري/عملي", max_length=10, choices=Section.choices, default=Section.THEORY)
    date = models.DateField("التاريخ")
    start_time = models.TimeField("وقت البداية")
    end_time = models.TimeField("وقت النهاية")
    room = models.CharField("القاعة", max_length=50, blank=True)
    # ملف Excel للحضور اللي ينرسل للأستاذ بعد المحاضرة
    report_file = models.FileField("ملف الحضور", upload_to="attendance_reports/", blank=True)
    report_sent_at = models.DateTimeField("وقت إرسال الملف للأستاذ", blank=True, null=True)

    class Meta:
        verbose_name = "محاضرة"
        verbose_name_plural = "المحاضرات"
        ordering = ["-date", "-start_time"]
        constraints = [
            models.CheckConstraint(condition=Q(end_time__gt=models.F("start_time")), name="session_end_after_start"),
        ]

    def __str__(self):
        return f"{self.offering.subject.name} - {self.date}"


class AttendanceRecord(models.Model):
    """حضور طالب بمحاضرة."""

    class Status(models.TextChoices):
        PRESENT = "present", "حاضر"
        LATE = "late", "متأخر"
        ABSENT = "absent", "غائب"
        EXCUSED = "excused", "مجاز"

    class Method(models.TextChoices):
        RFID = "rfid", "كارت RFID"
        MANUAL = "manual", "يدوي من الأستاذ"

    session = models.ForeignKey(LectureSession, on_delete=models.CASCADE, related_name="attendance")
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="attendance")
    status = models.CharField("الحالة", max_length=10, choices=Status.choices, default=Status.PRESENT)
    method = models.CharField("طريقة التسجيل", max_length=10, choices=Method.choices, default=Method.RFID)
    scanned_at = models.DateTimeField("وقت التسجيل", blank=True, null=True)
    # نتيجة التحقق من الوجه بالكاميرا (فارغ = بعد ما صار تحقق)
    face_verified = models.BooleanField("تم التحقق من الوجه", null=True, blank=True)
    face_match_score = models.FloatField("نسبة التطابق", null=True, blank=True)
    verification_photo = models.ImageField(
        "صورة وقت الحضور", upload_to="attendance_photos/", blank=True, null=True
    )

    class Meta:
        verbose_name = "سجل حضور"
        verbose_name_plural = "سجلات الحضور"
        constraints = [
            models.UniqueConstraint(fields=["session", "student"], name="one_attendance_per_session"),
        ]


# =====================================================================
# 7) مشاريع التخرج (المرحلة الرابعة)
# =====================================================================

class GraduationProject(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "مسودة"
        SUBMITTED = "submitted", "مُرسل للمشرف"
        APPROVED = "approved", "مقبول"

    title = models.CharField("اسم المشروع", max_length=250)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT)
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    supervisor = models.ForeignKey(
        TeacherProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="supervised_projects",
        verbose_name="المشرف",
    )
    features = models.TextField("خصائص المشروع", blank=True)
    objectives = models.TextField("أهداف المشروع", blank=True)
    challenges = models.TextField("المشاكل والتحديات", blank=True)
    conclusion = models.TextField("الخلاصة", blank=True)
    future_work = models.TextField("العمل المستقبلي", blank=True)
    hardware_description = models.TextField("وصف الهاردوير", blank=True)
    external_design_description = models.TextField("وصف الشكل الخارجي", blank=True)
    status = models.CharField("الحالة", max_length=10, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "مشروع تخرج"
        verbose_name_plural = "مشاريع التخرج"

    def __str__(self):
        return self.title


class ProjectMember(models.Model):
    """أعضاء فريق المشروع (المشروع عادة مجموعة طلاب)."""

    project = models.ForeignKey(GraduationProject, on_delete=models.CASCADE, related_name="members")
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="project_memberships")
    is_leader = models.BooleanField("قائد الفريق", default=False)

    class Meta:
        verbose_name = "عضو مشروع"
        verbose_name_plural = "أعضاء المشاريع"
        constraints = [
            models.UniqueConstraint(fields=["project", "student"], name="unique_project_member"),
        ]

    def clean(self):
        if self.student_id and self.student.current_stage != 4:
            raise ValidationError("مشروع التخرج بس لطلاب المرحلة الرابعة")


class ProjectImage(models.Model):
    """صور الشكل الخارجي للمشروع."""

    project = models.ForeignKey(GraduationProject, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField("الصورة", upload_to="projects/images/")
    caption = models.CharField("وصف الصورة", max_length=200, blank=True)

    class Meta:
        verbose_name = "صورة مشروع"
        verbose_name_plural = "صور المشاريع"


class ProjectHardwareItem(models.Model):
    """قطع الهاردوير المستخدمة بالمشروع."""

    project = models.ForeignKey(GraduationProject, on_delete=models.CASCADE, related_name="hardware_items")
    name = models.CharField("اسم القطعة", max_length=150)  # مثلاً Arduino Uno
    quantity = models.PositiveSmallIntegerField("العدد", default=1)
    notes = models.CharField("ملاحظات", max_length=200, blank=True)

    class Meta:
        verbose_name = "قطعة هاردوير"
        verbose_name_plural = "قطع الهاردوير"


# =====================================================================
# 8) الشات بوت والإشعارات
# =====================================================================

class FAQ(models.Model):
    """أسئلة وأجوبة الشات بوت (نفس محتوى qustion.csv بس بالداتابيس)."""

    question = models.TextField("السؤال")
    answer = models.TextField("الجواب")
    intent = models.CharField("التصنيف (Intent)", max_length=100, blank=True)
    is_active = models.BooleanField("فعّال", default=True)
    # متجه معنى السؤال (pgvector) للبحث الدلالي. ينحسب بالأمر: python manage.py embed_faqs
    embedding = VectorField(dimensions=TEXT_DIM, blank=True, null=True, editable=False)

    class Meta:
        verbose_name = "سؤال شائع"
        verbose_name_plural = "أسئلة الشات بوت"
        indexes = [
            HnswIndex(name="faq_embedding_hnsw", fields=["embedding"],
                      m=16, ef_construction=64, opclasses=["vector_cosine_ops"]),
        ]

    def __str__(self):
        return self.question[:60]


class ChatLog(models.Model):
    """سجل محادثات الشات بوت (حتى نعرف شنو الأسئلة اللي ينسألها الطلاب)."""

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)  # فارغ = زائر قبل التسجيل
    session_key = models.CharField(max_length=64, blank=True)
    message = models.TextField("رسالة الطالب")
    reply = models.TextField("رد البوت")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "محادثة"
        verbose_name_plural = "سجل المحادثات"
        ordering = ["-created_at"]


class Notification(models.Model):
    """إشعارات: "ملخصك انقبل"، "نزلت درجاتك"، ..."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField("العنوان", max_length=150)
    message = models.TextField("الرسالة", blank=True)
    link = models.CharField("رابط", max_length=300, blank=True)
    is_read = models.BooleanField("مقروء", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "إشعار"
        verbose_name_plural = "الإشعارات"
        ordering = ["-created_at"]
