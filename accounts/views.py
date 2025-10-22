from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.contrib.sessions.models import Session

from .forms import RegistrationForm
from .models import User


def register(request):
    """
    Handle user registration
    - Display registration form (GET)
    - Process form submission and send verification email (POST)
    """
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Create user but don't save to database yet
            user = form.save(commit=False)
            user.is_verified = False  # User must verify email first
            user.is_active = True  # Allow login but restrict features
            user.save()

            # Generate verification token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            # Build verification URL
            current_site = get_current_site(request)
            verification_link = (
                f"http://{current_site.domain}/accounts/verify-email/{uid}/{token}/"
            )

            # Send verification email
            subject = "Verify Your CampusNest Account"
            message = f"""
            Hi {user.first_name},
            # noqa: W293
            Welcome to CampusNest! Please verify your email address by clicking the link below:
            # noqa: W293
            {verification_link}
            # noqa: W293
            This link will expire in 24 hours.
            # noqa: W293
            If you didn't create this account, please ignore this email.
            # noqa: W293
            Best regards,
            The CampusNest Team
            """

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            messages.success(
                request,
                "Registration successful! Please check your email to verify your account.",
            )
            return redirect("register")
    else:
        form = RegistrationForm()

    return render(request, "accounts/register.html", {"form": form})


def verify_email(request, uidb64, token):
    """
    Verify user's email address using token from email link
    """
    try:
        # Decode user ID from URL
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    # Check if token is valid
    if user is not None and default_token_generator.check_token(user, token):
        user.is_verified = True
        user.save()
        messages.success(request, "Email verified successfully! You can now log in.")
        return redirect("login")
    else:
        messages.error(request, "Verification link is invalid or has expired.")
        return redirect("resend_verification")


def user_login(request):
    """
    Handle user login
    """
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=email, password=password)

            if user is not None:
                if user.is_verified:
                    login(request, user)
                    messages.success(request, f"Welcome back, {user.first_name}!")
                    return redirect("view_profile")
                else:
                    messages.error(
                        request, "Please verify your email before logging in."
                    )
                    # Store email in session for resend page
                    request.session["unverified_email"] = user.email
                    return redirect("resend_verification")
            else:
                messages.error(request, "Invalid email or password.")
    else:
        form = AuthenticationForm()

    return render(request, "accounts/login.html", {"form": form})


def user_logout(request):
    """
    Handle user logout
    """
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("login")


def resend_verification(request):
    """
    Resend verification email to user
    """
    if request.method == "POST":
        email = request.POST.get("email")

        try:
            user = User.objects.get(email=email)

            # Check if already verified
            if user.is_verified:
                messages.info(
                    request, "This email is already verified. You can log in."
                )
                return redirect("login")

            # Generate new verification token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            # Build verification URL
            current_site = get_current_site(request)
            verification_link = (
                f"http://{current_site.domain}/accounts/verify-email/{uid}/{token}/"
            )

            # Send verification email
            subject = "Verify Your CampusNest Account"
            message = f"""
            Hi {user.first_name},
            # noqa: W293
            You requested a new verification link for your CampusNest account.
            # noqa: W293
            Please verify your email address by clicking the link below:
            # noqa: W293
            {verification_link}
            # noqa: W293
            This link will expire in 24 hours.
            # noqa: W293
            If you didn't request this, please ignore this email.
            # noqa: W293
            Best regards,
            The CampusNest Team
            """

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            messages.success(
                request, "Verification email sent! Please check your inbox."
            )
            return redirect("resend_verification")

        except User.DoesNotExist:
            messages.error(request, "No account found with this email address.")

    # Pre-fill email if coming from login
    initial_email = request.session.get("unverified_email", "")
    if initial_email:
        del request.session["unverified_email"]

    return render(
        request, "accounts/resend_verification.html", {"initial_email": initial_email}
    )


def password_reset_request(request):
    """
    Handle password reset request - send reset email
    """
    if request.method == "POST":
        email = request.POST.get("email")

        try:
            user = User.objects.get(email=email)

            # Generate password reset token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            # Build reset URL
            current_site = get_current_site(request)
            reset_link = (
                f"http://{current_site.domain}/accounts/password-reset/{uid}/{token}/"
            )

            # Send password reset email
            subject = "Reset Your CampusNest Password"
            message = f"""
            Hi {user.first_name},
            # noqa: W293
            You requested to reset your password for your CampusNest account.
            # noqa: W293
            Click the link below to reset your password:
            # noqa: W293
            {reset_link}
            # noqa: W293
            This link will expire in 1 hour for security reasons.
            # noqa: W293
            If you didn't request this password reset, please ignore this email and your password will remain unchanged.
            # noqa: W293
            Best regards,
            The CampusNest Team
            """

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            messages.success(
                request, "Password reset email sent! Please check your inbox."
            )
            return redirect("password_reset_request")

        except User.DoesNotExist:
            # Don't reveal if email exists for security
            messages.success(
                request,
                "If an account exists with this email, you will receive password reset instructions.",
            )
            return redirect("password_reset_request")

    return render(request, "accounts/password_reset_request.html")


def password_reset_confirm(request, uidb64, token):
    """
    Handle password reset confirmation - validate token and set new password
    """
    try:
        # Decode user ID from URL
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    # Check if token is valid (1 hour expiry is built into default_token_generator)
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                # Save new password
                form.save()

                # Terminate all active sessions for this user (security)
                terminate_user_sessions(user)

                # Send confirmation email
                subject = "Your CampusNest Password Has Been Changed"
                message = f"""
            Hi {user.first_name},
            # noqa: W293
            This is to confirm that your password for CampusNest has been successfully changed.
            # noqa: W293
            If you did not make this change, please contact us immediately.
            # noqa: W293
            For security, all your active sessions have been logged out. Please log in again with your new password.
            # noqa: W293
            Best regards,
            The CampusNest Team
            """

                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )

                messages.success(
                    request,
                    "Password reset successful! You can now log in with your new password.",
                )
                return redirect("login")
        else:
            form = SetPasswordForm(user)

        return render(request, "accounts/password_reset_confirm.html", {"form": form})
    else:
        messages.error(
            request,
            "Password reset link is invalid or has expired. Please request a new one.",
        )
        return redirect("password_reset_request")


def terminate_user_sessions(user):
    """
    Terminate all active sessions for a specific user
    This is called when password is reset for security
    """
    user_sessions = []
    all_sessions = Session.objects.all()

    for session in all_sessions:
        session_data = session.get_decoded()
        if session_data.get("_auth_user_id") == str(user.id):
            user_sessions.append(session.pk)

    # Delete all sessions for this user
    Session.objects.filter(pk__in=user_sessions).delete()
