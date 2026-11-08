from django.contrib.auth import views as auth_views
from django.urls import path

from . import teacher_views as t
from . import views as v
from .forms import LoginForm

urlpatterns = [
    # ما قبل التسجيل
    path("", v.home, name="home"),
    # التسجيل والدخول
    path("register/", v.register, name="register"),
    path("login/", auth_views.LoginView.as_view(
        template_name="university/login.html", authentication_form=LoginForm, redirect_authenticated_user=True,
    ), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("after-login/", v.after_login, name="after_login"),
    path("verify/<uidb64>/<token>/", v.verify_email, name="verify_email"),
    path("verify/resend/", v.resend_verification, name="resend_verification"),
    path("notifications/", v.notifications, name="notifications"),

    # الطالب
    path("dashboard/", v.dashboard, name="dashboard"),
    path("subjects/<int:offering_id>/", v.subject_detail, name="subject_detail"),
    path("subjects/<int:offering_id>/summaries/new/", v.summary_upload, name="summary_upload"),
    path("summaries/<int:summary_id>/rate/", v.summary_rate, name="summary_rate"),
    path("project/", v.project_edit, name="project_edit"),
    path("project/submit/", v.project_submit, name="project_submit"),
    path("project/add/<str:what>/", v.project_add, name="project_add"),
    path("project/remove/<str:what>/<int:item_id>/", v.project_remove, name="project_remove"),

    # الأستاذ
    path("teacher/", t.dashboard, name="teacher_dashboard"),
    path("teacher/offerings/<int:offering_id>/", t.offering_detail, name="teacher_offering"),
    path("teacher/offerings/<int:offering_id>/materials/add/", t.material_add, name="teacher_material_add"),
    path("teacher/materials/<int:material_id>/delete/", t.material_delete, name="teacher_material_delete"),
    path("teacher/summaries/<int:summary_id>/<str:action>/", t.summary_review, name="teacher_summary_review"),
    path("teacher/offerings/<int:offering_id>/assessments/add/", t.assessment_add, name="teacher_assessment_add"),
    path("teacher/assessments/<int:assessment_id>/", t.assessment_detail, name="teacher_assessment"),
    path("teacher/assessments/<int:assessment_id>/toggle/", t.assessment_toggle, name="teacher_assessment_toggle"),
    path("teacher/assessments/<int:assessment_id>/import/", t.assessment_import, name="teacher_assessment_import"),
    path("teacher/assessments/<int:assessment_id>/template/", t.assessment_template, name="teacher_assessment_template"),
    path("teacher/offerings/<int:offering_id>/sessions/add/", t.session_add, name="teacher_session_add"),
    path("teacher/sessions/<int:session_id>/", t.session_detail, name="teacher_session"),
    path("teacher/sessions/<int:session_id>/report/", t.session_report, name="teacher_session_report"),
    path("teacher/projects/", t.projects, name="teacher_projects"),
    path("teacher/projects/<int:project_id>/<str:action>/", t.project_status, name="teacher_project_status"),
]
