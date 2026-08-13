from django.urls import path

from .views import (
    google_login,
    update_location,
    login,
    employee_locations,
    employee_location_history,
    location_history,
    employee_history_dates,
    history_by_date,
    upload_visit_proof
)

urlpatterns = [

    path("google-login/", google_login),

    path("update-location/", update_location),

    path("login/", login),

    path("employee-locations/", employee_locations),

    path(
        "employee-history/<int:employee_id>/",
        employee_location_history
    ),

    path(
        "location-history/<int:employee_id>/",
        location_history
    ),

    path(
    "history-dates/<int:employee_id>/",
    employee_history_dates),

    path(
    "history-by-date/<int:employee_id>/<str:date>/",
    history_by_date),

    path(
    "upload-visit-proof/",
    upload_visit_proof
),

]