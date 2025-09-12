from django.urls import path
from . import views

urlpatterns = [
    path("", views.login_view, name="login"),
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("logout/", views.logout_view, name="logout"),

    # Dashboards
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("counselor-dashboard/", views.counselor_dashboard, name="counselor_dashboard"),
    path("nutritionist-dashboard/", views.nutritionist_dashboard, name="nutritionist_dashboard"),

    # Leads
    path("leads/", views.leads_management, name="leads_management"),
    path("leads/update/<str:lead_id>/", views.update_lead_status, name="update_lead_status"),
    path("leads/assign/<str:lead_id>/", views.assign_lead, name="assign_lead"),
    path("leads/convert/<str:lead_id>/", views.convert_lead_to_customer, name="convert_lead_to_customer"),

    # Instagram Webhook (Real-time DM Sync)
    path("webhook/instagram/", views.instagram_webhook, name="instagram_webhook"),

    # Customers
    path("customers/", views.customers_management, name="customers_management"),
    # path("customers/update-progress/<str:customer_id>/", views.update_progress, name="update_progress"),

    path("plans-management/", views.plans_management, name="plans_management"),
    path("whatsapp-management/", views.whatsapp_management, name="whatsapp_management"),
    path("reports-analytics/", views.reports_analytics, name="reports_analytics"),
    path("user-management/", views.user_management, name="user_management"),

]
