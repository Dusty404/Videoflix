from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.core import signing
from django.core.mail import send_mail

signer = signing.TimestampSigner(salt="email-activation")

def send_confirmation_email(user):
    token = signer.sign_object({"user_id": str(user.pk), "email": user.email})
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    activation_url = f"http://localhost:8000/api/activate/{uidb64}/{token}/"
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
    return signer.unsign_object(token, max_age=60 * 60 * 24)
