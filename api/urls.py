from django.urls import path
from django.conf.urls import include
from rest_framework import routers
from knox import views as knox_views
from .api_views import ResumeViewSet, LoginAPI, UserViewSet
router = routers.DefaultRouter()
router.register('resume', ResumeViewSet)
router.register('user', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('login/', LoginAPI.as_view()),
    path('logout/', knox_views.LogoutView.as_view(), name='knox_logout'),
    # path('parser/', apiviews.elections_view, name='elections_view'),
]