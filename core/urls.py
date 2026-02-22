from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls), # Django'ning o'z admin paneli
    path('', include('maktab.urls')),  # Boshqa barcha sahifalar core ilovasiga yo'naltiriladi
]