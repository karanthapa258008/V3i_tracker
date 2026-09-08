from django.shortcuts import render
from datetime import datetime
from django.utils import timezone

from google.oauth2 import id_token
from google.auth.transport import requests

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import (
    Employee,
    LocationLog,
    CurrentLocation,
    VisitProof,
    TrackingSession,
    LocationEvent
)

from django.core.files.storage import default_storage
from django.conf import settings

from django.db.models.functions import TruncDate


GOOGLE_CLIENT_ID = "215426541202-dfle5hgascifn83u4e7fcp74kaj2cnr0.apps.googleusercontent.com"


# =========================================================
# GOOGLE LOGIN
# =========================================================

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
        employee.login_type = "google"
        employee.save()

        return Response({

            "status": True,

            "employee_id": employee.id,

            "name": employee.name,

            "email": employee.email,

            "photo": (
                request.build_absolute_uri(
                    employee.profile_photo.url
                )
                if employee.profile_photo
                else None
            ),

            "role": employee.role

        })

    except Exception as e:

        return Response({

            "status": False,

            "message": str(e)

        }, status=400)


# =========================================================
# UPDATE LOCATION
# =========================================================

@api_view(["POST"])
def update_location(request):

    print(request.data)

    employee_id = request.data.get("employee_id")
    latitude = request.data.get("latitude")
    longitude = request.data.get("longitude")
    accuracy = request.data.get("accuracy", 0)

    if not employee_id:

        return Response({

            "status": False,

            "message": "Employee ID required"

        }, status=400)

    try:

        employee = Employee.objects.get(
            id=employee_id,
            role="employee",
            is_active=True
        )

        # =====================================================
        # SAVE LOCATION HISTORY
        # =====================================================

        location = LocationLog.objects.create(

            employee=employee,

            latitude=latitude,

            longitude=longitude,

            accuracy=accuracy

        )

        # =====================================================
        # UPDATE CURRENT LOCATION
        # =====================================================

        CurrentLocation.objects.update_or_create(

            employee=employee,

            defaults={

                "latitude": latitude,

                "longitude": longitude,

                "accuracy": accuracy

            }

        )

        # =====================================================
        # TRACKING SESSION
        # =====================================================

        active_session = TrackingSession.objects.filter(

            employee=employee,

            is_active=True

        ).first()

        # =====================================================
        # FIRST LOCATION
        # =====================================================

        if active_session is None:

            active_session = TrackingSession.objects.create(

                employee=employee,

                start_time=location.created_at,

                end_time=location.created_at,

                is_active=True

            )

        # =====================================================
        # LAST LOCATION
        # =====================================================

        else:

            active_session.end_time = location.created_at

            active_session.save(
                update_fields=["end_time"]
            )

        return Response({

            "status": True,

            "message": "Location Updated",

            "start_time": timezone.localtime(
                active_session.start_time
            ).strftime("%Y-%m-%d %I:%M:%S %p"),

            "end_time": timezone.localtime(
                active_session.end_time
            ).strftime("%Y-%m-%d %I:%M:%S %p")

        })

    except Employee.DoesNotExist:

        return Response({

            "status": False,

            "message": "Employee not found"

        }, status=404)


# =========================================================
# SIMPLE LOGIN
# =========================================================

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

        "photo": (

            request.build_absolute_uri(
                employee.profile_photo.url
            )

            if employee.profile_photo

            else None

        ),

        "role": employee.role

    })


# =========================================================
# ADD EMPLOYEE
# =========================================================

@api_view(["POST"])
def add_employee(request):

    name = request.data.get("name")
    email = request.data.get("email")
    role = request.data.get("role", "employee")

    profile_photo = request.FILES.get("profile_photo")

    # -----------------------------------------------------
    # NAME CHECK
    # -----------------------------------------------------

    if not name:

        return Response({

            "status": False,

            "message": "Name is required"

        }, status=400)

    # -----------------------------------------------------
    # EMAIL CHECK
    # -----------------------------------------------------

    if not email:

        return Response({

            "status": False,

            "message": "Email is required"

        }, status=400)

    # -----------------------------------------------------
    # ROLE CHECK
    # -----------------------------------------------------

    if role not in ["admin", "employee"]:

        return Response({

            "status": False,

            "message": "Invalid role"

        }, status=400)

    # -----------------------------------------------------
    # DUPLICATE EMAIL CHECK
    # -----------------------------------------------------

    if Employee.objects.filter(
        email=email
    ).exists():

        return Response({

            "status": False,

            "message": "Employee with this email already exists"

        }, status=400)

    # -----------------------------------------------------
    # CREATE EMPLOYEE
    # -----------------------------------------------------

    employee = Employee.objects.create(

        name=name,

        email=email,

        role=role,

        profile_photo=profile_photo,

        is_active=True,

        login_type="email"

    )

    # -----------------------------------------------------
    # PROFILE PHOTO URL
    # -----------------------------------------------------

    photo_url = None

    if employee.profile_photo:

        photo_url = request.build_absolute_uri(

            employee.profile_photo.url

        )

    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------

    return Response({

        "status": True,

        "message": "Employee added successfully",

        "employee": {

            "employee_id": employee.id,

            "name": employee.name,

            "email": employee.email,

            "role": employee.role,

            "is_active": employee.is_active,

            "profile_photo": photo_url

        }

    }, status=201)


# =========================================================
# ALL EMPLOYEE LIVE LOCATIONS
# =========================================================

@api_view(["GET"])
def employee_locations(request):

    data = []

    # ONLY EMPLOYEES
    employees = Employee.objects.filter(
        role="employee",
        is_active=True
    ).order_by("id")

    for employee in employees:

        # Current location find karo
        current_location = CurrentLocation.objects.filter(
            employee=employee
        ).first()

        # -------------------------------------------------
        # PROFILE PHOTO
        # -------------------------------------------------

        profile_photo_url = None

        if employee.profile_photo:

            profile_photo_url = request.build_absolute_uri(
                employee.profile_photo.url
            )

        # -------------------------------------------------
        # DEFAULT VALUES
        # -------------------------------------------------

        latitude = None
        longitude = None
        accuracy = None
        updated_at = None
        online = False

        # -------------------------------------------------
        # CURRENT LOCATION AVAILABLE
        # -------------------------------------------------

        if current_location:

            latitude = float(
                current_location.latitude
            )

            longitude = float(
                current_location.longitude
            )

            accuracy = float(
                current_location.accuracy
            )

            updated_at = timezone.localtime(
                current_location.updated_at
            ).isoformat()

            # -------------------------------------------------
            # ONLINE / OFFLINE
            # -------------------------------------------------

            last_seen = current_location.updated_at

            online = (
                timezone.now() - last_seen
            ).total_seconds() <= 5 * 60

        # -------------------------------------------------
        # EMPLOYEE DATA
        # -------------------------------------------------

        data.append({

            "employee_id": employee.id,

            "name": employee.name,

            "email": employee.email,

            "profile_photo": profile_photo_url,

            "latitude": latitude,

            "longitude": longitude,

            "accuracy": accuracy,

            "updated_at": updated_at,

            "online": online,

            "role": employee.role,

            "is_active": employee.is_active

        })

    return Response({

        "status": True,

        "employees": data

    })
# =========================================================
# EMPLOYEE LOCATION HISTORY
# =========================================================

@api_view(["GET"])
def employee_location_history(request, employee_id):

    try:

        employee = Employee.objects.get(
            id=employee_id,
            role="employee",
            is_active=True
        )

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

            "latitude": float(
                item.latitude
            ),

            "longitude": float(
                item.longitude
            ),

            "accuracy": item.accuracy,

            "created_at": item.created_at

        })

    return Response({

        "status": True,

        "employee_id": employee.id,

        "employee_name": employee.name,

        "history": data

    })


# =========================================================
# LOCATION HISTORY
# =========================================================

@api_view(["GET"])
def location_history(request, employee_id):

    try:

        employee = Employee.objects.get(
            id=employee_id,
            role="employee",
            is_active=True
        )

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

            "latitude": float(
                item.latitude
            ),

            "longitude": float(
                item.longitude
            ),

            "accuracy": item.accuracy,

            "created_at": item.created_at

        })

    return Response({

        "status": True,

        "history": data

    })


# =========================================================
# EMPLOYEE HISTORY DATES
# =========================================================

@api_view(["GET"])
def employee_history_dates(request, employee_id):

    try:

        employee = Employee.objects.get(
            id=employee_id,
            role="employee",
            is_active=True
        )

    except Employee.DoesNotExist:

        return Response({

            "status": False,

            "message": "Employee not found"

        }, status=404)

    dates = (

        LocationLog.objects

        .filter(employee=employee)

        .annotate(
            day=TruncDate("created_at")
        )

        .values_list(
            "day",
            flat=True
        )

        .distinct()

        .order_by("-day")

    )

    data = []

    for date in dates:

        data.append({

            "date": date.strftime(
                "%Y-%m-%d"
            )

        })

    return Response({

        "status": True,

        "dates": data

    })


# =========================================================
# HISTORY BY DATE
# =========================================================

@api_view(["GET"])
def history_by_date(request, employee_id, date):

    try:

        employee = Employee.objects.get(
            id=employee_id,
            role="employee",
            is_active=True
        )

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

        .prefetch_related(
            "visit_proofs"
        )

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

            "latitude": float(
                item.latitude
            ),

            "longitude": float(
                item.longitude
            ),

            "accuracy": item.accuracy,

            "time": timezone.localtime(
                item.created_at
            ).strftime("%I:%M %p"),

            "created_at": timezone.localtime(
                item.created_at
            ),

            "has_photo": proof is not None,

            "photo": photo_url

        })

    return Response({

        "status": True,

        "employee_name": employee.name,

        "date": date,

        "history": data

    })


# =========================================================
# UPLOAD VISIT PROOF
# =========================================================

@api_view(["POST"])
def upload_visit_proof(request):

    employee_id = request.data.get(
        "employee_id"
    )

    latitude = request.data.get(
        "latitude"
    )

    longitude = request.data.get(
        "longitude"
    )

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

            "status": False,

            "message": "Employee id required"

        }, status=400)

    if not photo:

        return Response({

            "status": False,

            "message": "Photo required"

        }, status=400)

    try:

        employee = Employee.objects.get(
            id=employee_id,
            role="employee",
            is_active=True
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

            "status": True,

            "message": "Visit proof uploaded",

            "photo": proof.photo.url

        })

    except Employee.DoesNotExist:

        return Response({

            "status": False,

            "message": "Employee not found"

        }, status=404)


# =========================================================
# UPDATE PROFILE PHOTO
# =========================================================

@api_view(["POST"])
def update_profile_photo(request):

    employee_id = request.data.get(
        "employee_id"
    )

    photo = request.FILES.get(
        "profile_photo"
    )

    if not employee_id:

        return Response({

            "status": False,

            "message": "Employee ID required"

        }, status=400)

    if not photo:

        return Response({

            "status": False,

            "message": "Profile photo required"

        }, status=400)

    try:

        employee = Employee.objects.get(
            id=employee_id,
            role="employee",
            is_active=True
        )

        # Delete old profile photo
        if employee.profile_photo:

            employee.profile_photo.delete(
                save=False
            )

        # Save new profile photo
        employee.profile_photo = photo

        employee.save()

        photo_url = request.build_absolute_uri(

            employee.profile_photo.url

        )

        return Response({

            "status": True,

            "message": "Profile photo updated successfully",

            "employee_id": employee.id,

            "name": employee.name,

            "email": employee.email,

            "profile_photo": photo_url

        })

    except Employee.DoesNotExist:

        return Response({

            "status": False,

            "message": "Employee not found"

        }, status=404)


# =========================================================
# LOCATION EVENT
# =========================================================

@api_view(["POST"])
def location_event(request):

    employee_id = request.data.get("employee_id")
    event_type = request.data.get("event_type")
    event_time = request.data.get("event_time")

    latitude = request.data.get("latitude")
    longitude = request.data.get("longitude")

    # -----------------------------------------------------
    # REQUIRED DATA CHECK
    # -----------------------------------------------------

    if not employee_id:

        return Response({
            "status": False,
            "message": "Employee ID required"
        }, status=400)

    if not event_type:

        return Response({
            "status": False,
            "message": "Event type required"
        }, status=400)

    if event_type not in [
        "gps_off",
        "gps_on",
        "internet_off",
        "internet_on"
    ]:

        return Response({
            "status": False,
            "message": "Invalid event type"
        }, status=400)

    try:

        # -------------------------------------------------
        # ONLY EMPLOYEE
        # -------------------------------------------------

        employee = Employee.objects.get(
            id=employee_id,
            role="employee",
            is_active=True
        )

        # -------------------------------------------------
        # EVENT TIME
        # -------------------------------------------------

        if event_time:

            try:

                event_time = datetime.fromisoformat(
                    event_time.replace("Z", "+00:00")
                )

                if timezone.is_naive(event_time):

                    event_time = timezone.make_aware(
                        event_time
                    )

            except Exception:

                event_time = timezone.now()

        else:

            event_time = timezone.now()

        # -------------------------------------------------
        # SAVE EVENT
        # -------------------------------------------------

        event = LocationEvent.objects.create(

            employee=employee,

            event_type=event_type,

            event_time=event_time,

            latitude=latitude if latitude else None,

            longitude=longitude if longitude else None

        )

        return Response({

            "status": True,

            "message": "Location event saved",

            "event": {

                "id": event.id,

                "employee_id": employee.id,

                "employee_name": employee.name,

                "employee_email": employee.email,

                "event_type": event.event_type,

                "event_time": timezone.localtime(
                    event.event_time
                ).strftime(
                    "%Y-%m-%d %I:%M:%S %p"
                )

            }

        }, status=201)

    except Employee.DoesNotExist:

        return Response({

            "status": False,

            "message": "Employee not found"

        }, status=404)

    except Exception as e:

        return Response({

            "status": False,

            "message": str(e)

        }, status=400)


# =========================================================
# LOCATION EVENT HISTORY
# =========================================================

@api_view(["GET"])
def location_event_history(request, employee_id):

    try:

        employee = Employee.objects.get(
            id=employee_id,
            role="employee",
            is_active=True
        )

    except Employee.DoesNotExist:

        return Response({

            "status": False,

            "message": "Employee not found"

        }, status=404)

    # -----------------------------------------------------
    # GET ALL EVENTS
    # -----------------------------------------------------

    events = LocationEvent.objects.filter(

        employee=employee

    ).order_by("-event_time")

    data = []

    for event in events:

        data.append({

            "id": event.id,

            "employee_id": employee.id,

            "employee_name": employee.name,

            "employee_email": employee.email,

            "event_type": event.event_type,

            "event_label": event.get_event_type_display(),

            "event_time": timezone.localtime(
                event.event_time
            ).strftime(
                "%Y-%m-%d %I:%M:%S %p"
            ),

            "latitude": (
                float(event.latitude)
                if event.latitude is not None
                else None
            ),

            "longitude": (
                float(event.longitude)
                if event.longitude is not None
                else None
            ),

            "created_at": timezone.localtime(
                event.created_at
            ).strftime(
                "%Y-%m-%d %I:%M:%S %p"
            )

        })

    return Response({

        "status": True,

        "employee_id": employee.id,

        "employee_name": employee.name,

        "employee_email": employee.email,

        "total_events": len(data),

        "events": data

    })


@api_view(["POST"])
def heartbeat(request):
    employee_id = request.data.get("employee_id")

    if not employee_id:
        return Response(
            {
                "status": False,
                "message": "Employee ID required"
            },
            status=400
        )

    try:
        employee = Employee.objects.get(
            id=employee_id,
            role="employee",
            is_active=True
        )
    except Employee.DoesNotExist:
        return Response(
            {
                "status": False,
                "message": "Employee not found"
            },
            status=404
        )

    current_location = CurrentLocation.objects.filter(
        employee=employee
    ).first()

    if not current_location:
        return Response(
            {
                "status": False,
                "message": "Current location not found"
            },
            status=404
        )

    current_location.updated_at = timezone.now()

    current_location.save(
        update_fields=["updated_at"]
    )

    return Response(
        {
            "status": True,
            "message": "Heartbeat received",
            "employee_id": employee.id,
            "updated_at": timezone.localtime(
                current_location.updated_at
            ).isoformat()
        },
        status=200
    )