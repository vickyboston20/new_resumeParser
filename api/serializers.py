from rest_framework import serializers
from .models import Resume, UserDetails, User, UserProfile
from django.contrib.auth import authenticate
from knox.models import AuthToken


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('empId', 'dob', 'phone_number')


class UserSerializer(serializers.HyperlinkedModelSerializer):
    """
    Bifrost user writable nested serializer
    """
    profile = UserProfileSerializer(required=True)

    class Meta:
        model = User
        fields = ('url', 'email', 'first_name', 'last_name', 'password', 'profile')
        extra_kwargs = {'password': {'write_only': True, 'required': True}}

    def create(self, validated_data):
        profile_data = validated_data.pop('profile')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        UserProfile.objects.create(user=user, **profile_data)
        AuthToken.objects.create(user)
        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile')
        profile = instance.profile

        instance.email = validated_data.get('email', instance.email)
        instance.save()

        profile.empId = profile_data.get('empId', profile.empId)
        profile.dob = profile_data.get('dob', profile.dob)
        profile.phone_number = profile_data.get('phone_number', profile.phone_number)
        profile.save()
        return instance


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Incorrect Credentials")


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDetails
        fields = ('user', 'name', 'email', 'mobile_number', 'education', 'educations', 'skills', 'experience', 'experiences', 'uploaded_on')


class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ('user', 'resume', 'last_uploaded_on')