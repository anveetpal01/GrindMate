"""URL routes for /api/v1/auth/."""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

app_name = "users"

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", views.MeView.as_view(), name="me"),
    path("change-password/", views.ChangePasswordView.as_view(), name="change_password"),
    path("verify-email/", views.VerifyEmailView.as_view(), name="verify_email"),
    path(
        "resend-verification/",
        views.ResendVerificationView.as_view(),
        name="resend_verification",
    ),
    path(
        "password-reset/request/",
        views.PasswordResetRequestView.as_view(),
        name="password_reset_request",
    ),
    path(
        "password-reset/confirm/",
        views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
]
