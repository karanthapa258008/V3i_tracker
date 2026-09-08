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
    upload_visit_proof,
    update_profile_photo,
    add_employee,
    location_event,
    location_event_history,
    heartbeat,
)


urlpatterns = [

    # =====================================================
    # LOGIN
    # =====================================================

    path(
        "google-login/",
        google_login,
        name="google-login"
    ),

    path(
        "login/",
        login,
        name="login"
    ),


    # =====================================================
    # LOCATION
    # =====================================================

    path(
        "update-location/",update_location,name="update-location"),

    path("employee-locations/",employee_locations,name="employee-locations"),

    path(
        "employee-history/<int:employee_id>/",
        employee_location_history,
        name="employee-history"
    ),

    path(
        "location-history/<int:employee_id>/",
        location_history,
        name="location-history"
    ),

    path(
        "history-dates/<int:employee_id>/",
        employee_history_dates,
        name="history-dates"
    ),

    path(
        "history-by-date/<int:employee_id>/<str:date>/",
        history_by_date,
        name="history-by-date"
    ),


    # =====================================================
    # VISIT PROOF
    # =====================================================

    path(
        "upload-visit-proof/",
        upload_visit_proof,
        name="upload-visit-proof"
    ),


    # =====================================================
    # PROFILE
    # =====================================================

    path(
        "update-profile-photo/",
        update_profile_photo,
        name="update-profile-photo"
    ),

    path(
        "add-employee/",
        add_employee,
        name="add-employee"
    ),


    # =====================================================
    # LOCATION EVENTS
    # =====================================================

    path(
        "location-event/",
        location_event,
        name="location-event"
    ),

    path(
        "location-event-history/<int:employee_id>/",
        location_event_history,
        name="location-event-history"
    ),
    path("heartbeat/", heartbeat, name="heartbeat"),
]