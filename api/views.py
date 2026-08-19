from django.shortcuts import render
from datetime import datetime

from google.oauth2 import id_token
from google.auth.transport import requests
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import (
    Employee,
    LocationLog,
    CurrentLocation,
    VisitProof
)
from django.core.files.storage import default_storage
from django.conf import settings

from django.db.models.functions import TruncDate


GOOGLE_CLIENT_ID = "215426541202-dfle5hgascifn83u4e7fcp74kaj2cnr0.apps.googleusercontent.com"


# ---------------- GOOGLE LOGIN ---------------- #

@api_view(["POST"])
def google_login(request):

    token = request.data.get("id_token")

    if not token:
        return Response({
            "status": False,
            "message": "ID Token missing"
        }, status=400)

    try:

        info = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            GOOGLE_CLIENT_ID
        )

        google_id = info["sub"]
        name = info.get("name", "")
        email = info.get("email", "")
        photo = info.get("picture", "")

        try:
            employee = Employee.objects.get(email=email)

        except Employee.DoesNotExist:
            return Response({
                "status": False,
                "message": "You are not authorized to use this application."
            }, status=404)

        # Account Active Check
        if not employee.is_active:
            return Response({
                "status": False,
                "message": "Account is disabled."
            }, status=403)

        # Update Google Details
        employee.google_id = google_id
        employee.name = name
        employee.profile_photo = photo
        employee.login_type = "google"
        employee.save()

        return Response({
            "status": True,
            "employee_id": employee.id,
            "name": employee.name,
            "email": employee.email,
            "photo": employee.profile_photo,
            "role": employee.role
        })

    except Exception as e:

        return Response({
            "status": False,
            "message": str(e)
        }, status=400)

# ---------------- UPDATE LOCATION ---------------- #

@api_view(["POST"])
def update_location(request):

    print(request.data)

    employee_id = request.data.get("employee_id")
    latitude = request.data.get("latitude")
    longitude = request.data.get("longitude")
    accuracy = request.data.get("accuracy", 0)

    try:

        employee = Employee.objects.get(id=employee_id)

        # Save History
        LocationLog.objects.create(
            employee=employee,
            latitude=latitude,
            longitude=longitude,
            accuracy=accuracy
        )

        # Update Current Location
        CurrentLocation.objects.update_or_create(
            employee=employee,
            defaults={
                "latitude": latitude,
                "longitude": longitude,
                "accuracy": accuracy
            }
        )

        return Response({
            "status": True,
            "message": "Location Updated"
        })

    except Employee.DoesNotExist:

        return Response({
            "status": False,
            "message": "Employee not found"
        }, status=404)


# ---------------- SIMPLE LOGIN (TEMP) ---------------- #

# ---------------- SIMPLE LOGIN ---------------- #

@api_view(["POST"])
def login(request):

    email = request.data.get("email")
    name = request.data.get("name")

    if not email:
        return Response({
            "status": False,
            "message": "Email Required"
        }, status=400)

    try:

        employee = Employee.objects.get(
            email=email
        )

    except Employee.DoesNotExist:

        return Response({
            "status": False,
            "message": "You are not authorized to use this application."
        }, status=404)


    if not employee.is_active:

        return Response({
            "status": False,
            "message": "Account is disabled."
        }, status=403)


    # Name update
    if name:

        employee.name = name

        employee.save()


    return Response({

        "status": True,

        "employee_id": employee.id,

        "name": employee.name,

        "email": employee.email,

        "photo": employee.profile_photo,

        "role": employee.role

    })
# ---------------- ALL EMPLOYEE LIVE LOCATIONS ---------------- #

@api_view(["GET"])
def employee_locations(request):

    data = []

    locations = CurrentLocation.objects.select_related("employee")

    for item in locations:

        data.append({

            "employee_id": item.employee.id,

            "name": item.employee.name,

            "email": item.employee.email,

            "profile_photo": item.employee.profile_photo,

            "latitude": float(item.latitude),

            "longitude": float(item.longitude),

            "accuracy": item.accuracy,

            "updated_at": item.updated_at

        })

    return Response({
        "status": True,
        "employees": data
    })



# ---------------- EMPLOYEE LOCATION HISTORY ---------------- #

@api_view(["GET"])
def employee_location_history(request, employee_id):

    try:

        employee = Employee.objects.get(id=employee_id)

    except Employee.DoesNotExist:

        return Response({
            "status": False,
            "message": "Employee not found"
        }, status=404)

    history = LocationLog.objects.filter(
        employee=employee
    ).order_by("-created_at")

    data = []

    for item in history:

        data.append({

            "latitude": float(item.latitude),

            "longitude": float(item.longitude),

            "accuracy": item.accuracy,

            "created_at": item.created_at

        })

    return Response({

        "status": True,

        "employee_id": employee.id,

        "employee_name": employee.name,

        "history": data

    })



@api_view(["GET"])
def location_history(request, employee_id):

    try:

        employee = Employee.objects.get(id=employee_id)

    except Employee.DoesNotExist:

        return Response({
            "status": False,
            "message": "Employee not found"
        })

    history = LocationLog.objects.filter(
        employee=employee
    ).order_by("-created_at")

    data = []

    for item in history:

        data.append({

            "latitude": float(item.latitude),

            "longitude": float(item.longitude),

            "accuracy": item.accuracy,

            "created_at": item.created_at

        })

    return Response({

        "status": True,

        "history": data

    })

@api_view(["GET"])
def employee_history_dates(request, employee_id):

    try:

        employee = Employee.objects.get(id=employee_id)

    except Employee.DoesNotExist:

        return Response({
            "status": False,
            "message": "Employee not found"
        }, status=404)

    dates = (
        LocationLog.objects
        .filter(employee=employee)
        .annotate(day=TruncDate("created_at"))
        .values_list("day", flat=True)
        .distinct()
        .order_by("-day")
    )

    data = []

    for date in dates:

        data.append({
            "date": date.strftime("%Y-%m-%d")
        })

    return Response({
        "status": True,
        "dates": data
    })



@api_view(["GET"])
def history_by_date(request, employee_id, date):

    try:
        employee = Employee.objects.get(id=employee_id)

    except Employee.DoesNotExist:
        return Response({
            "status": False,
            "message": "Employee not found"
        }, status=404)

    try:
        selected_date = datetime.strptime(
            date,
            "%Y-%m-%d"
        ).date()

    except Exception:
        return Response({
            "status": False,
            "message": "Invalid date format"
        }, status=400)

    history = (
        LocationLog.objects
        .filter(
            employee=employee,
            created_at__date=selected_date
        )
        .prefetch_related("visit_proofs")
        .order_by("created_at")
    )

    data = []

    for item in history:

        # Is location point par VisitProof hai ya nahi
        proof = item.visit_proofs.first()

        photo_url = None

        if proof and proof.photo:
            photo_url = request.build_absolute_uri(
                proof.photo.url
            )

        data.append({

            "latitude": float(item.latitude),

            "longitude": float(item.longitude),

            "accuracy": item.accuracy,

            "time": item.created_at.strftime("%I:%M %p"),

            "created_at": item.created_at,

            "has_photo": proof is not None,

            "photo": photo_url

        })

    return Response({

        "status": True,

        "employee_name": employee.name,

        "date": date,

        "history": data

    })



@api_view(["POST"])
def upload_visit_proof(request):

    employee_id = request.data.get("employee_id")

    latitude = request.data.get("latitude")

    longitude = request.data.get("longitude")

    accuracy = request.data.get(
        "accuracy",
        0
    )

    address = request.data.get(
        "address",
        ""
    )

    photo = request.FILES.get(
        "photo"
    )


    if not employee_id:
        return Response({
            "status":False,
            "message":"Employee id required"
        },status=400)


    if not photo:
        return Response({
            "status":False,
            "message":"Photo required"
        },status=400)


    try:

        employee = Employee.objects.get(
            id=employee_id
        )


        # Latest location save
        location = LocationLog.objects.create(

            employee=employee,

            latitude=latitude,

            longitude=longitude,

            accuracy=accuracy

        )


        # Photo save
        proof = VisitProof.objects.create(

            location_log=location,

            employee=employee,

            photo=photo,

            latitude=latitude,

            longitude=longitude,

            accuracy=accuracy,

            address=address

        )


        return Response({

            "status":True,

            "message":"Visit proof uploaded",

            "photo":proof.photo.url

        })


    except Employee.DoesNotExist:


        return Response({

            "status":False,

            "message":"Employee not found"

        },status=404)