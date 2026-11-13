"""
تفعيل pgvector:
  - تفعيل إضافة vector بالداتابيس (تحتاج مستخدم superuser أول مرة: enable_pgvector.bat)
  - بصمة الوجه تتحول من double precision[] إلى vector(128)
  - متجه معنى لأسئلة الشات بوت vector(768)
  - فهارس HNSW للبحث السريع عن أقرب متجه
"""
import pgvector.django
from django.db import migrations
from pgvector.django import VectorExtension


class Migration(migrations.Migration):

    dependencies = [
        ("university", "0002_project_image_label"),
    ]

    operations = [
        VectorExtension(),
        # البصمات الموجودة تتحول تلقائياً (pgvector يدعم التحويل من مصفوفة أرقام)
        migrations.AlterField(
            model_name="studentprofile",
            name="face_embedding",
            field=pgvector.django.VectorField(blank=True, dimensions=128, null=True, verbose_name="بصمة الوجه"),
        ),
        migrations.AddField(
            model_name="faq",
            name="embedding",
            field=pgvector.django.VectorField(blank=True, dimensions=768, editable=False, null=True),
        ),
        migrations.AddIndex(
            model_name="studentprofile",
            index=pgvector.django.HnswIndex(
                ef_construction=64, fields=["face_embedding"], m=16,
                name="student_face_hnsw", opclasses=["vector_l2_ops"],
            ),
        ),
        migrations.AddIndex(
            model_name="faq",
            index=pgvector.django.HnswIndex(
                ef_construction=64, fields=["embedding"], m=16,
                name="faq_embedding_hnsw", opclasses=["vector_cosine_ops"],
            ),
        ),
    ]
