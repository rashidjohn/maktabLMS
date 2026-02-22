from django.urls import path
from . import views

urlpatterns = [
    # Asosiy tizimga kirish va chiqish
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_user, name='logout'),

    # O'quvchi va O'qituvchi panellari
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('quiz/<int:quiz_id>/', views.take_quiz, name='take_quiz'),
    path('student/results/', views.student_results, name='student_results'),

    # Admin Panelining maxsus sahifalari
    path('admin-panel/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/create-user/', views.create_user, name='create_user'),
    path('admin-panel/results/', views.all_results_admin, name='all_results_admin'),
    path('admin-panel/upload-excel/', views.upload_quiz_excel, name='upload_quiz_excel'),

    # Admin Panelidagi ma'lumot jadvallari (Ro'yxatlar)
    path('admin-panel/classes/', views.manage_classes, name='manage_classes'),
    path('admin-panel/subjects/', views.manage_subjects, name='manage_subjects'),
    path('admin-panel/quizzes/', views.manage_quizzes, name='manage_quizzes'),
    path('admin-panel/students/', views.manage_students, name='manage_students'),
    path('admin-panel/teachers/', views.manage_teachers, name='manage_teachers'),
]