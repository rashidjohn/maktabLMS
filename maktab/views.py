from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Quiz, CustomUser, ClassRoom, Result, Question, Answer, Subject


# ==========================================
# 1. TIZIMGA KIRISH (LOGIN)
# ==========================================
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        jshshir_kiritilgan = request.POST.get('jshshir')
        parol_kiritilgan = request.POST.get('password')
        user = authenticate(request, username=jshshir_kiritilgan, password=parol_kiritilgan)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'login.html', {'error': 'JSHSHIR yoki parol xato!'})
    return render(request, 'login.html')


def logout_user(request):
    logout(request)
    return redirect('login')


# ==========================================
# 2. ROLLAR BO'YICHA YO'NALTIRISH (HOME)
# ==========================================
@login_required(login_url='login')
def home_view(request):
    user = request.user
    if user.role == 'admin' or user.is_superuser:
        return redirect('admin_dashboard')
    elif user.role == 'teacher':
        return redirect('teacher_dashboard')
    elif user.role == 'student':
        return redirect('student_dashboard')
    else:
        return redirect('logout')


# ==========================================
# 3. O'QUVCHI PANELI (STUDENT DASHBOARD)
# ==========================================
@login_required(login_url='login')
def student_dashboard(request):
    if request.user.role != 'student':
        return redirect('home')

    student_class = request.user.classroom
    student_results = Result.objects.filter(student=request.user)
    completed_quiz_ids = student_results.values_list('quiz_id', flat=True)
    available_quizzes = Quiz.objects.filter(classroom=student_class).exclude(id__in=completed_quiz_ids)

    context = {
        'available_quizzes': available_quizzes,
        'student_results': student_results,
        'classroom': student_class
    }
    return render(request, 'student_panel/my_exams.html', context)


@login_required(login_url='login')
def take_quiz(request, quiz_id):
    if request.user.role != 'student':
        return redirect('home')

    quiz = get_object_or_404(Quiz, id=quiz_id)

    if quiz.classroom != request.user.classroom:
        return redirect('student_dashboard')

    if Result.objects.filter(student=request.user, quiz=quiz).exists():
        return redirect('student_results')

    # BAZADA 150 TA BO'LSA HAM, HAR DOIM 20 TA RANDOM OLINADI
    QUESTIONS_LIMIT = 20
    # Agar mabodo bazada savol 20 taga yetmasa, borini oladi (masalan 15 ta bo'lsa)
    actual_total_questions = min(quiz.questions.count(), QUESTIONS_LIMIT)

    if request.method == 'POST':
        correct_answers = 0

        for key, value in request.POST.items():
            if key.startswith('question_'):
                answer_id = int(value)
                is_correct = Answer.objects.filter(id=answer_id, is_correct=True).exists()
                if is_correct:
                    correct_answers += 1

        # FOIZNI HISOBLASH
        score = (correct_answers / actual_total_questions) * 100 if actual_total_questions > 0 else 0

        Result.objects.create(
            student=request.user,
            quiz=quiz,
            score=round(score, 1),
            correct_answers=correct_answers,
            total_questions=actual_total_questions  # Jami savolni ham bazaga saqlaymiz
        )
        return redirect('student_results')

    # EKRANGA 20 TA TASODIFIY (RANDOM) SAVOLNI CHIQARISH
    questions = quiz.questions.all().order_by('?')[:QUESTIONS_LIMIT]
    return render(request, 'student_panel/take_quiz.html', {'quiz': quiz, 'questions': questions})

# ==========================================
# 4. SINF RAHBARI PANELI (TEACHER DASHBOARD)
# ==========================================
@login_required(login_url='login')
def teacher_dashboard(request):
    if request.user.role != 'teacher':
        return redirect('home')

    if hasattr(request.user, 'managed_class'):
        managed_class = request.user.managed_class
        students = managed_class.students.all()
    else:
        managed_class = None
        students = []

    context = {
        'classroom': managed_class,
        'students': students
    }
    return render(request, 'teacher_panel/my_class.html', context)


# ==========================================
# 5. ADMIN PANEL VA TUGMALAR
# ==========================================
@login_required(login_url='login')
def admin_dashboard(request):
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('home')
    context = {
        'students_count': CustomUser.objects.filter(role='student').count(),
        'teachers_count': CustomUser.objects.filter(role='teacher').count(),
        'classes_count': ClassRoom.objects.count(),
        'quizzes_count': Quiz.objects.count(),
    }
    return render(request, 'admin_panel/dashboard.html', context)


@login_required(login_url='login')
def create_user(request):
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('home')

    if request.method == 'POST':
        try:
            user = CustomUser.objects.create_user(
                jshshir=request.POST.get('jshshir'),
                password=request.POST.get('password'),
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name'),
                role=request.POST.get('role')
            )
            classroom_id = request.POST.get('classroom')
            if request.POST.get('role') == 'student' and classroom_id:
                user.classroom_id = classroom_id
                user.save()
            return redirect('admin_dashboard')
        except Exception as e:
            classrooms = ClassRoom.objects.all()
            return render(request, 'admin_panel/create_user.html',
                          {'classrooms': classrooms, 'error': "Xatolik: Bunday JSHSHIR band yoki ma'lumot xato!"})

    classrooms = ClassRoom.objects.all()
    return render(request, 'admin_panel/create_user.html', {'classrooms': classrooms})


@login_required(login_url='login')
def upload_quiz_excel(request):
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('home')

    if request.method == 'POST':
        quiz_id = request.POST.get('quiz_id')
        excel_file = request.FILES.get('excel_file')

        if not quiz_id or not excel_file:
            messages.error(request, "Iltimos, testni ham, Excel faylni ham tanlang!")
            return redirect('upload_quiz_excel')

        try:
            import pandas as pd
            quiz = Quiz.objects.get(id=quiz_id)
            df = pd.read_excel(excel_file)

            for index, row in df.iterrows():
                question = Question.objects.create(quiz=quiz, text=str(row['Savol']))
                correct_letter = str(row['Togri_javob']).strip().upper()
                Answer.objects.create(question=question, text=str(row['A']), is_correct=(correct_letter == 'A'))
                Answer.objects.create(question=question, text=str(row['B']), is_correct=(correct_letter == 'B'))
                Answer.objects.create(question=question, text=str(row['C']), is_correct=(correct_letter == 'C'))
                Answer.objects.create(question=question, text=str(row['D']), is_correct=(correct_letter == 'D'))

            messages.success(request, f"Ajoyib! {len(df)} ta savol muvaffaqiyatli yuklandi.")
            return redirect('admin_dashboard')
        except Exception as e:
            messages.error(request,
                           f"Faylni o'qishda xatolik ketdi. Ustun nomlari to'g'riligini tekshiring! Xato: {str(e)}")
            return redirect('upload_quiz_excel')

    quizzes = Quiz.objects.all().order_by('-id')
    return render(request, 'admin_panel/upload_excel.html', {'quizzes': quizzes})


# ==========================================
# 6. ADMIN JADVALLARI (Ro'yxatlar)
# ==========================================
@login_required(login_url='login')
def all_results_admin(request):
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('home')
    all_results = Result.objects.all().order_by('-completed_at')
    return render(request, 'admin_panel/all_results.html', {'results': all_results})


@login_required(login_url='login')
def manage_classes(request):
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('home')
    classes = ClassRoom.objects.all()
    return render(request, 'admin_panel/classes_list.html', {'classes': classes})


@login_required(login_url='login')
def manage_subjects(request):
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('home')
    subjects = Subject.objects.all()
    return render(request, 'admin_panel/subjects_list.html', {'subjects': subjects})


@login_required(login_url='login')
def manage_quizzes(request):
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('home')
    quizzes = Quiz.objects.all().order_by('-id')
    return render(request, 'admin_panel/quizzes_list.html', {'quizzes': quizzes})


@login_required(login_url='login')
def manage_students(request):
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('home')
    students = CustomUser.objects.filter(role='student').order_by('classroom', 'last_name')
    return render(request, 'admin_panel/students_list.html', {'students': students})


@login_required(login_url='login')
def manage_teachers(request):
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('home')
    teachers = CustomUser.objects.filter(role='teacher').order_by('last_name')
    return render(request, 'admin_panel/teachers_list.html', {'teachers': teachers})

# ==========================================
# ==========================================
# 12. O'QUVCHINING ISHLAGAN TESTLARI
# ==========================================
@login_required(login_url='login')
def student_results(request):
    # Faqat o'quvchilar kira oladi
    if request.user.role != 'student':
        return redirect('home')

    # O'quvchining o'zi ishlagan barcha testlarini bazadan tortib olamiz
    # E'tibor bering: HTML dagi 'student_results' so'zi shu yerdan ketyapti
    results = Result.objects.filter(student=request.user).order_by('-completed_at')

    return render(request, 'student_panel/my_results.html', {'student_results': results})

# ==========================================
# 4. SINF RAHBARI PANELI (TEACHER DASHBOARD)
# ==========================================
@login_required(login_url='login')
def teacher_dashboard(request):
    if request.user.role != 'teacher':
        return redirect('home')

    if hasattr(request.user, 'managed_class'):
        managed_class = request.user.managed_class
        # Sinfdagi barcha o'quvchilarni olamiz
        students = managed_class.students.all()
        # FAQAT shu sinf o'quvchilarining test natijalarini olamiz
        class_results = Result.objects.filter(student__in=students).order_by('-completed_at')
    else:
        managed_class = None
        students = []
        class_results = []

    context = {
        'classroom': managed_class,
        'students': students,
        'class_results': class_results, # Mana shu qator eng muhimi!
    }
    return render(request, 'teacher_panel/my_class.html', context)