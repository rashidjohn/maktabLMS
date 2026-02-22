from django.contrib import admin
from .models import CustomUser, ClassRoom, Subject, Quiz, Question, Answer, Result

# ------------------------------------------------
# FOYDALANUVCHI UCHUN TOZA ADMIN SOZLAMASI
# ------------------------------------------------
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('jshshir', 'first_name', 'last_name', 'role', 'classroom')
    list_filter = ('role', 'classroom')
    search_fields = ('jshshir', 'first_name', 'last_name')
    fields = ('jshshir', 'password', 'first_name', 'last_name', 'role', 'classroom', 'is_active', 'is_staff', 'is_superuser')

    def save_model(self, request, obj, form, change):
        if obj.pk:
            orig_obj = CustomUser.objects.get(pk=obj.pk)
            if obj.password != orig_obj.password:
                obj.set_password(obj.password)
        else:
            obj.set_password(obj.password)
        super().save_model(request, obj, form, change)

# ------------------------------------------------
# SINF VA O'QUVCHILAR SONI UCHUN SOZLAMA
# ------------------------------------------------
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'language', 'teacher', 'get_student_count')
    list_filter = ('language',)
    search_fields = ('name',)

    def get_student_count(self, obj):
        return obj.students.count()
    get_student_count.short_description = "O'quvchilar soni"

# ------------------------------------------------
# SAVOLLAR VA VARIANTLAR UCHUN SOZLAMALAR
# ------------------------------------------------
class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 4

class QuestionAdmin(admin.ModelAdmin):
    inlines = [AnswerInline]
    list_display = ('text', 'quiz')
    list_filter = ('quiz',)
    search_fields = ('text',)

# ------------------------------------------------
# QOLGAN JADVALLAR
# ------------------------------------------------
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'classroom', 'duration_minutes')
    list_filter = ('subject', 'classroom')

class ResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'quiz', 'score', 'completed_at')
    list_filter = ('quiz', 'student')

# Barchasini ro'yxatdan o'tkazamiz
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(ClassRoom, ClassRoomAdmin)
admin.site.register(Subject)
admin.site.register(Quiz, QuizAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Result, ResultAdmin)