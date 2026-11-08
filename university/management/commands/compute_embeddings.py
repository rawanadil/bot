"""
يحسب بصمة الوجه لكل طالبة عندها صورة حية بس ما عندها بصمة.
يحتاج مكتبة face_recognition:  pip install face_recognition
التشغيل: python manage.py compute_embeddings
"""
from django.core.management.base import BaseCommand

from university.models import StudentProfile
from university.services import compute_face_embedding


class Command(BaseCommand):
    help = "حساب بصمة الوجه من الصور الحية"

    def handle(self, *args, **options):
        try:
            import face_recognition  # noqa: F401
        except ImportError:
            self.stderr.write("نصبي المكتبة أولاً: pip install face_recognition")
            return
        done = 0
        for s in StudentProfile.objects.filter(face_embedding__isnull=True).exclude(live_photo=""):
            with s.live_photo.open("rb") as f:
                emb = compute_face_embedding(f)
            if emb:
                s.face_embedding = emb
                s.save(update_fields=["face_embedding"])
                done += 1
            else:
                self.stdout.write(f"ما لگينا وجه بصورة {s}")
        self.stdout.write(f"انحسبت {done} بصمة.")
