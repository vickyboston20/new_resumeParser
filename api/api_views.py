from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import viewsets, status, permissions
from rest_framework.permissions import IsAuthenticated
from .models import Resume, UserDetails, User
from .serializers import UserSerializer, LoginSerializer, UserDetailSerializer, ResumeSerializer
from .permissions import IsLoggedInUserOrAdmin, IsAdminUser
from rest_framework.permissions import AllowAny
from rest_framework import generics
from knox.models import AuthToken
from rest_framework.parsers import FileUploadParser


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    # Add this code block
    # def get_permissions(self):
    #     permission_classes = []
    #     if self.action == 'create':
    #         permission_classes = [AllowAny]
    #     elif self.action == 'retrieve' or self.action == 'update' or self.action == 'partial_update':
    #         permission_classes = [IsLoggedInUserOrAdmin]
    #     elif self.action == 'list' or self.action == 'destroy':
    #         permission_classes = [IsAdminUser]
    #     return [permission() for permission in permission_classes]


class LoginAPI(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        return Response({
            "user": UserSerializer(user, context=self.get_serializer_context()).data,
            "token": AuthToken.objects.create(user)[1]
        })


class UserViewSet(viewsets.ModelViewSet):
    # permission_classes = [
    #     permissions.IsAuthenticated,
    # ]
    queryset = UserDetails.objects.all()
    serializer_class = UserDetailSerializer

    def get_permissions(self):
        permission_classes = []
        if self.action == 'create' or self.action == 'destroy':
            permission_classes = [IsAdminUser]
        elif self.action == 'update' or self.action == 'partial_update':
            permission_classes = [IsAdminUser]
        elif self.action == 'list' or self.action == 'retrieve':
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]


class ResumeViewSet(viewsets.ModelViewSet):
    parser_class = (FileUploadParser,)
    # permission_classes = [
    #     permissions.IsAuthenticated,
    # ]
    queryset = Resume.objects.all()
    serializer_class = ResumeSerializer

    def get_permissions(self):
        permission_classes = []
        if self.action == 'create' or self.action == 'destroy':
            permission_classes = [IsAdminUser]
        elif self.action == 'update' or self.action == 'partial_update':
            permission_classes = [IsAdminUser]
        elif self.action == 'list' or self.action == 'retrieve':
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]


@api_view(['POST'])
@permission_classes([IsAuthenticated,])
def resume_view(request, resume_id):
    user = request.user
    print(user)
    election = get_object_or_404(UserDetails, pk=resume_id)
    serializer = UserDetailSerializer(data=request.data)
    if serializer.is_valid():
        choice = serializer.save(election=election)
        return Response(ChoiceSerializer(choice).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)