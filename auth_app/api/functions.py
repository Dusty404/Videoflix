from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from datetime import timedelta
from django.core.signing import TimestampSigner
from django.core.mail import send_mail


def send_confirmation_email(user):

    signer = TimestampSigner(salt="account-activation")
    token = signer.sign(str(user.pk))
    #original = signer.unsign(value)

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