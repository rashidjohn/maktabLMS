from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

# ==========================================
# 1. FOYDALANUVCHI MENEJERI (JSHSHIR uchun)
# ==========================================
class CustomUserManager(BaseUserManager):
    def create_user(self, jshshir, password=None, **extra_fields):
        if not jshshir:
            raise ValueError('JSHSHIR kiritilishi shart!')
        if len(jshshir) != 14 or not jshshir.isdigit():
            raise ValueError('JSHSHIR 14 ta raqamdan iborat bo\'lishi kerak!')

        user = self.model(jshshir=jshshir, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, jshshir, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser is_staff=True bo\'lishi kerak.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser is_superuser=True bo\'lishi kerak.')

        return self.create_user(jshshir, password, **extra_fields)

# ==========================================
# 2. FOYDALANUVCHI MODELI (Custom User)
# ==========================================
class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('teacher', 'Teacher (Sinf rahbari)'),
        ('student', 'Student'),
    )

    username = None
    jshshir = models.CharField(max_length=14, unique=True, verbose_name="JSHSHIR")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    classroom = models.ForeignKey('ClassRoom', on_delete=models.SET_NULL, null=True, blank=True, related_name='students')

    USERNAME_FIELD = 'jshshir'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    objects = CustomUserManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.jshshir})"

# ==========================================
# 3. SINF MODELI
# ==========================================
class ClassRoom(models.Model):
    LANGUAGE_CHOICES = (
        ('uz', 'O\'zbek tili'),
        ('ru', 'Rus tili'),
    )
    name = models.CharField(max_length=50, verbose_name="Sinf nomi (Masalan: 6-A)")
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, verbose_name="Ta'lim tili")
    teacher = models.OneToOneField(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
        limit_choices_to={'role': 'teacher'}, related_name='managed_class', verbose_name="Sinf rahbari"
    )

    def __str__(self):
        return f"{self.name} ({self.get_language_display()})"

# ==========================================
# 4. FAN MODELI
# ==========================================
class Subject(models.Model):
    name = models.CharField(max_length=100, verbose_name="Fan nomi")
    classrooms = models.ManyToManyField(ClassRoom, related_name='subjects', verbose_name="Qaysi sinflarda o'tiladi?")

    def __str__(self):
        return self.name

# ==========================================
# 5. TEST (QUIZ) MODELI
# ==========================================
class Quiz(models.Model):
    title = models.CharField(max_length=200, verbose_name="Test nomi (M: 1-chorak yakuniy)")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='quizzes')
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='quizzes')
    duration_minutes = models.PositiveIntegerField(help_text="Test ishlash vaqti (daqiqa)")
    pass_score = models.FloatField(default=50.0, help_text="O'tish bali (%)")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.subject.name} ({self.classroom.name})"

# ==========================================
# 6. SAVOL MODELI
# ==========================================
class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField(verbose_name="Savol matni")

    def __str__(self):
        return self.text

# ==========================================
# 7. JAVOB VARIANTLARI (A, B, C, D)
# ==========================================
class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=255, verbose_name="Variant matni")
    is_correct = models.BooleanField(default=False, verbose_name="To'g'ri javobmi?")

    def __str__(self):
        return f"{self.text} {'(Tog`ri)' if self.is_correct else ''}"

# ==========================================
# 8. NATIJA MODELI
# ==========================================
class Result(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'student'}, related_name='results')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='results')
    score = models.FloatField(verbose_name="To'plangan foiz yoki ball")
    correct_answers = models.PositiveIntegerField(default=0, verbose_name="To'g'ri javoblar soni")
    total_questions = models.PositiveIntegerField(default=20, verbose_name="Jami berilgan savollar soni")
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.first_name} - {self.quiz.title} ({self.score}%)"