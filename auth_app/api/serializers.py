from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User

class RegistrationSerializer(serializers.ModelSerializer):
    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'confirmed_password']
        extra_kwargs = {
            'password': {
                'write_only': True
            },
            'email': {
                'required': True
            }
        }

    def validate_confirmed_password(self, value):
        """
        Check that the supplied password confirmation matches the password.

        Args:
            value (str): Submitted password confirmation.

        Returns:
            str: The validated confirmation.

        Raises:
            ValidationError: If the supplied password values differ.
        """
        password = self.initial_data.get('password')
        if password and value and password != value:
            raise serializers.ValidationError('Passwords do not match')
        return value

    def validate_email(self, value):
        """
        Reject an email address already stored using an exact lookup.

        Args:
            value (str): Submitted email address.

        Returns:
            str: The email address if no exact match exists.

        Raises:
            ValidationError: If the email address already exists.
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already exists')
        return value

    def save(self):
        """
        Create an inactive user from validated data with a hashed password.

        Use the email address as both the username and email.

        Returns:
            User: The newly saved inactive account.
        """
        pw = self.validated_data['password']
        email = self.validated_data['email']

        account = User(email=email, username=email, is_active=False)
        account.set_password(pw)
        account.save()
        return account

User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def __init__(self, *args, **kwargs):
        """
        Initialize email-based login fields and remove the username field.

        Args:
            *args: Positional arguments forwarded to the parent serializer.
            **kwargs: Keyword arguments forwarded to the parent serializer.

        Returns:
            None: This function does not return a value.
        """
        super().__init__(*args, **kwargs)

        if "username" in self.fields:
            self.fields.pop("username")

    def validate(self, attrs):
        """
        Resolve an email/password pair and delegate JWT creation to the parent.

        Args:
            attrs (dict): Input containing email and password.

        Returns:
            dict: Validated access and refresh token data.

        Raises:
            ValidationError: If the email is unknown or the password is incorrect.
            AuthenticationFailed: If parent authentication rejects the account.
        """
        email = attrs.get("email")
        password = attrs.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Ungültige Email oder Passwort")

        if not user.check_password(password):
            raise serializers.ValidationError("Ungültige Email oder Passwort")

        data = super().validate({"username": user.username, "password": password})
        return data

class CheckAccountForPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetSerializer(serializers.Serializer):
    password = serializers.CharField()
    confirm_password = serializers.CharField()

    def validate_confirm_password(self, value):
            """
            Check the confirmation against the submitted replacement password.

            Args:
                value (str): Submitted password confirmation.

            Returns:
                str: The validated confirmation.

            Raises:
                ValidationError: If the supplied password values differ.
            """
            password = self.initial_data.get('password')
            if password and value and password != value:
                raise serializers.ValidationError('Passwords do not match')
            return value