from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from apps.core import views as core
from apps.catalog import views as catalog
from apps.payments import views as pay
from apps.placements import views as placements
from apps.accounts import views as accounts
from apps.catalog import upload_views

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("", core.home, name="home"),
    path("accounts/register/", accounts.register, name="register"),
    path("accounts/verify/resend/", accounts.resend_verification, name="resend_verification"),
    path("accounts/verify/<str:token>/", accounts.verify_email, name="verify_email"),
    path("accounts/", include("django.contrib.auth.urls")),   # login, logout(POST), password reset/change
    path("dashboard/", accounts.dashboard, name="dashboard"),
    path("documents/upload/", upload_views.upload_document, name="upload_document"),
    path("documents/", catalog.document_list, name="documents"),
    path("documents/<slug:slug>/", catalog.document_detail, name="document_detail"),
    path("documents/<slug:slug>/buy/", pay.buy_document, name="buy_document"),
    path("download/document/<uuid:token>/", catalog.download_document, name="download_document"),
    path("payments/callback/", pay.callback, name="payment_callback"),
    path("payments/webhook/paystack/", pay.paystack_webhook, name="paystack_webhook"),
    path("nysc/", placements.listing, {"ptype": "nysc"}, name="nysc"),
    path("it-placement/", placements.listing, {"ptype": "it"}, name="it_placement"),
    path("jobs/", placements.listing, {"ptype": "job"}, name="jobs"),
]
