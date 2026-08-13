from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Employee,
    LocationLog,
    CurrentLocation,
    VisitProof
)



# ================= EMPLOYEE ADMIN =================

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





# ================= LOCATION HISTORY ADMIN =================

@admin.register(LocationLog)
class LocationLogAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "employee",
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
    )





# ================= CURRENT LOCATION ADMIN =================

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





# ================= VISIT PROOF ADMIN =================

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

    )



    readonly_fields = (

        "photo_preview",

    )




    def photo_preview(self, obj):

        if obj.photo:

            return format_html(

                '<img src="{}" width="120" height="120" style="object-fit:cover;"/>',

                obj.photo.url

            )


        return "No Photo"



    photo_preview.short_description = "Visit Photo"