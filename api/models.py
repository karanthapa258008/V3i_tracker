from django.db import models

class Employee(models.Model):

    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("employee", "Employee"),
    )

    google_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True
    )

    name = models.CharField(max_length=100)

    email = models.EmailField(unique=True)

    profile_photo = models.URLField(blank=True, null=True)

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="employee"
    )

    is_active = models.BooleanField(default=True)

    login_type = models.CharField(
        max_length=20,
        choices=[
            ("google", "Google"),
            ("email", "Email")
        ],
        default="email"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class LocationLog(models.Model):

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE
    )

    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7
    )

    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7
    )

    accuracy = models.FloatField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee.name} ({self.created_at})"





class CurrentLocation(models.Model):

    employee = models.OneToOneField(
        Employee,
        on_delete=models.CASCADE
    )

    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7
    )

    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7
    )

    accuracy = models.FloatField(default=0)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.employee.name



class VisitProof(models.Model):

    location_log = models.ForeignKey(
        "LocationLog",
        on_delete=models.CASCADE,
        related_name="visit_proofs"
    )

    employee = models.ForeignKey(
        "Employee",
        on_delete=models.CASCADE
    )

    photo = models.ImageField(
        upload_to="visit_proofs/"
    )

    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7
    )

    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7
    )

    accuracy = models.FloatField(default=0)

    address = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.employee.name} - Visit Proof"


class TrackingSession(models.Model):

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="tracking_sessions"
    )

    start_time = models.DateTimeField(
        auto_now_add=True
    )

    end_time = models.DateTimeField(
        null=True,
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    def __str__(self):
        return f"{self.employee.name} - {self.start_time}"