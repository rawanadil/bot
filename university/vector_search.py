"""
البحث بالمتجهات (pgvector) داخل PostgreSQL:
  - search_faqs: يلگى أقرب أسئلة الشات بوت بالمعنى (cosine distance)
  - find_face_match: يلگى أقرب طالبة لبصمة وجه (L2 distance)

موديل النصوص يتحمل مرة وحدة بس أول ما نحتاجه (lazy) لأنه كبير.
"""
from functools import lru_cache

from pgvector.django import CosineDistance, L2Distance

from . import models as m

TEXT_MODEL_NAME = "intfloat/multilingual-e5-base"  # نفس موديل boot2.py (768 رقم)

# face_recognition: مسافة أقل من 0.6 = نفس الشخص عادة
FACE_MATCH_THRESHOLD = 0.6


@lru_cache(maxsize=1)
def get_text_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(TEXT_MODEL_NAME)


def embed_passages(texts, batch_size=64):
    """متجهات للنصوص اللي نخزنها (موديل e5 يحتاج بادئة passage:)."""
    vectors = get_text_model().encode(
        ["passage: " + t for t in texts],
        batch_size=batch_size,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return [v.tolist() for v in vectors]


def embed_query(text):
    """متجه لسؤال المستخدم (موديل e5 يحتاج بادئة query:)."""
    return get_text_model().encode(
        "query: " + text, normalize_embeddings=True, convert_to_numpy=True
    ).tolist()


def search_faqs(query, k=20):
    """
    يرجع أقرب k أسئلة فعّالة. كل نتيجة بيها .distance (0 = نفس المعنى، 2 = عكسه)
    query: نص، أو متجه جاهز.
    """
    vector = embed_query(query) if isinstance(query, str) else query
    return list(
        m.FAQ.objects.filter(is_active=True, embedding__isnull=False)
        .annotate(distance=CosineDistance("embedding", vector))
        .order_by("distance")[:k]
    )


def faqs_are_indexed():
    return m.FAQ.objects.filter(is_active=True, embedding__isnull=False).exists()


def find_face_match(embedding, threshold=FACE_MATCH_THRESHOLD, queryset=None):
    """
    يلگى أقرب طالبة لبصمة الوجه. يرجع (الطالبة، المسافة) أو (None، المسافة).
    queryset: نكدر نحصر البحث (مثلاً طلاب المادة بس).
    """
    qs = queryset if queryset is not None else m.StudentProfile.objects.all()
    best = (
        qs.filter(face_embedding__isnull=False)
        .annotate(distance=L2Distance("face_embedding", list(embedding)))
        .order_by("distance")
        .first()
    )
    if best is None:
        return None, None
    return (best if best.distance <= threshold else None), best.distance
