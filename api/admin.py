from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Employee,
    LocationLog,
    CurrentLocation,
    VisitProof,
    LocationEvent
)


# =========================================================
# EMPLOYEE ADMIN
# =========================================================

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "email",
        "role",
        "login_type",
        "is_active",
        "created_at"
    )

    search_fields = (
        "name",
        "email"
    )

    list_filter = (
        "role",
        "login_type",
        "is_active",
        "created_at"
    )


# =========================================================
# LOCATION HISTORY ADMIN
# =========================================================

@admin.register(LocationLog)
class LocationLogAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "employee",
        "latitude",
        "longitude",
        "accuracy",
        "location_time"
    )

    search_fields = (
        "employee__name",
        "employee__email"
    )

    list_filter = (
        "created_at",
        "employee",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "employee",
        "latitude",
        "longitude",
        "accuracy",
        "created_at",
    )

    def location_time(self, obj):

        if obj.created_at:
            return obj.created_at.strftime(
                "%d-%m-%Y %I:%M:%S %p"
            )

        return "-"

    location_time.short_description = "Location Time"


# =========================================================
# CURRENT LOCATION ADMIN
# =========================================================

@admin.register(CurrentLocation)
class CurrentLocationAdmin(admin.ModelAdmin):

    list_display = (
        "employee",
        "latitude",
        "longitude",
        "accuracy",
        "updated_at"
    )

    search_fields = (
        "employee__name",
        "employee__email"
    )

    list_filter = (
        "employee",
    )

    ordering = (
        "-updated_at",
    )


# =========================================================
# VISIT PROOF ADMIN
# =========================================================

@admin.register(VisitProof)
class VisitProofAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "employee",
        "photo_preview",
        "latitude",
        "longitude",
        "accuracy",
        "created_at"
    )

    search_fields = (
        "employee__name",
        "employee__email"
    )

    list_filter = (
        "created_at",
        "employee",
    )

    readonly_fields = (
        "photo_preview",
    )

    def photo_preview(self, obj):

        if obj.photo:

            return format_html(
                '<img src="{}" width="120" height="120" '
                'style="object-fit:cover;"/>',
                obj.photo.url
            )

        return "No Photo"

    photo_preview.short_description = "Visit Photo"


# =========================================================
# LOCATION EVENT HISTORY ADMIN
# =========================================================

@admin.register(LocationEvent)
class LocationEventAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "employee",
        "event_type",
        "event_time_display",
        "latitude",
        "longitude",
        "created_at"
    )

    search_fields = (
        "employee__name",
        "employee__email",
    )

    list_filter = (
        "event_type",
        "employee",
        "created_at",
    )

    ordering = (
        "-event_time",
    )

    readonly_fields = (
        "employee",
        "event_type",
        "event_time",
        "latitude",
        "longitude",
        "created_at",
    )

    def event_time_display(self, obj):

        if obj.event_time:

            return obj.event_time.strftime(
                "%d-%m-%Y %I:%M:%S %p"
            )

        return "-"

    event_time_display.short_description = "Event Time"

