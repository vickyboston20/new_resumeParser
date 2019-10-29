from django.urls import path
from django.conf.urls import include
from rest_framework import routers
from knox import views as knox_views
from django.urls import path, re_path
from .api_views import ResumeViewSet, LoginAPI, UserViewSet, Parser
router = routers.DefaultRouter()
router.register('resume', ResumeViewSet)
router.register('user', UserViewSet)


urlpatterns = [
    path('', include(router.urls)),
    re_path(r'^parser/', Parser.as_view()),
    path('login/', LoginAPI.as_view()),
    path('logout/', knox_views.LogoutView.as_view(), name='knox_logout'),
    # path('parser/', apiviews.elections_view, name='elections_view'),
]