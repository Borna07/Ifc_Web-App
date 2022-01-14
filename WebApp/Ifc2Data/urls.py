from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload', views.model_upload, name='model_upload'),
    path('download', views.model_download, name='model_download'),
]