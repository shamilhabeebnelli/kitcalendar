from django.urls import path
from . import views
urlpatterns = [path("", views.home, name="home"), path("reservation/<int:pk>/action/", views.action, name="action"), path("equipment/new/", views.equipment, name="equipment")]
