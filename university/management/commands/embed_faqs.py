"""
يحسب متجه المعنى (pgvector) لأسئلة الشات بوت حتى يصير البحث الدلالي داخل الداتابيس.
يحتاج: pip install sentence-transformers
التشغيل:
  python manage.py embed_faqs          # الأسئلة اللي ما عندها متجه بس
  python manage.py embed_faqs --all    # يعيد حساب الكل (إذا تغير الموديل)
"""
from django.core.management.base import BaseCommand

from university.models import FAQ


class Command(BaseCommand):
    help = "حساب متجهات أسئلة الشات بوت (pgvector)"

    def add_arguments(self, parser):
        parser.add_argument("--all", action="store_true", help="إعادة حساب كل الأسئلة")
        parser.add_argument("--batch-size", type=int, default=64)

    def handle(self, *args, **options):
        try:
            from university.vector_search import embed_passages
        except ImportError:
            self.stderr.write("نصبي المكتبة أولاً: pip install sentence-transformers")
            return

        qs = FAQ.objects.all() if options["all"] else FAQ.objects.filter(embedding__isnull=True)
        faqs = list(qs.only("id", "question"))
        if not faqs:
            self.stdout.write("كل الأسئلة عندها متجهات.")
            return

        size = options["batch_size"]
        for start in range(0, len(faqs), size):
            chunk = faqs[start:start + size]
            for faq, vec in zip(chunk, embed_passages([f.question for f in chunk])):
                faq.embedding = vec
            FAQ.objects.bulk_update(chunk, ["embedding"])
            self.stdout.write(f"{min(start + size, len(faqs))}/{len(faqs)}")
        self.stdout.write(self.style.SUCCESS(f"انحسبت {len(faqs)} متجه."))
