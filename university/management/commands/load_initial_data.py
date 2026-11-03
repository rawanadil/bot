"""
يملي الداتابيس بالبيانات الموجودة أصلاً بالمشروع:
  - الأقسام من departments_utf8_bom.csv
  - أسئلة الشات بوت من qustion.csv

التشغيل: python manage.py load_initial_data
"""
import csv

from django.conf import settings
from django.core.management.base import BaseCommand

from university.models import FAQ, Department


class Command(BaseCommand):
    help = "تحميل الأقسام وأسئلة الشات بوت من ملفات CSV"

    def handle(self, *args, **options):
        base = settings.BASE_DIR

        with open(base / "departments_utf8_bom.csv", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                Department.objects.get_or_create(name=row["Department"].strip())
        self.stdout.write(f"الأقسام: {Department.objects.count()}")

        with open(base / "qustion.csv", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                if row.get("Question") and row.get("Answer"):
                    FAQ.objects.get_or_create(
                        question=row["Question"].strip(),
                        defaults={"answer": row["Answer"].strip(), "intent": (row.get("Intent") or "").strip()},
                    )
        self.stdout.write(f"أسئلة الشات بوت: {FAQ.objects.count()}")
