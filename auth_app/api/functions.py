from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.core import signing
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from urllib.parse import urlencode

registration_signer = signing.TimestampSigner(salt="email-activation")
password_reset_signer = signing.TimestampSigner(salt="password_reset")

def send_confirmation_email(user):
    token = registration_signer.sign(str(user.pk))
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    query_params = urlencode({"uid": uidb64, "token": token})
    activation_url = (f"http://127.0.0.1:5500/pages/auth/activate.html?{query_params}")
    username = user.email.split("@")[0]

    send_mail(
        subject=f"Dear {username}",
        message=(
            f"Dear {username},\n\n"
            "Thank you for registering with Videoflix. "
            "To complete your registration and verify your email address, "
            "please click the link below:\n\n"
            f"{activation_url}\n\n"
            "If you did not create an account with us, "
            "please disregard this email.\n\n"
            "Best regards,\n"
            "Your Videoflix Team"
        ),
        from_email="info@Videoflix.com",
        recipient_list=[user.email],
    )

def check_activation_token(token):
    return registration_signer.unsign(token, max_age=60 * 60 * 24)


def send_password_reset_email(user):
    token = default_token_generator.make_token(user)
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    query_params = urlencode({"uid": uidb64, "token": token})
    reset_url = f"http://127.0.0.1:5500/pages/auth/confirm_password.html?{query_params}"

    send_mail(
        subject=f"Reset your Password",
        message=(
            f"Hello,\n\n"
            "We recently received a request top reset your password if you made this request, please klick on the following link to reset your password:\n\n"
            f"{reset_url}\n\n"
            "If you did not request a password reset, "
            "please ignore this email.\n\n"
            "Best regards,\n"
            "Your Videoflix Team"
        ),
        from_email="info@Videoflix.com",
        recipient_list=[user.email],
    )