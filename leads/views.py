from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import LeadForm, LoginForm, UpdateForm
from .models import Employee, Lead, StatusUpdate

# Set URBANTENTS_PASSCODE in your project settings.py to override the default.
EMPLOYEE_PASSCODE = getattr(settings, "URBANTENTS_PASSCODE", "URBANTENTS2026")


def employee_required(view_func):
    """Simple session-based gate — not real auth, just keeps casual visitors out."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("employee_id"):
            return redirect("leads:login")
        return view_func(request, *args, **kwargs)

    return wrapper


def login_view(request):
    if request.session.get("employee_id"):
        return redirect("leads:dashboard")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            if form.cleaned_data["passcode"] != EMPLOYEE_PASSCODE:
                messages.error(request, "Galat passcode. Dobara try karein.")
            else:
                employee, _ = Employee.objects.get_or_create(name=form.cleaned_data["name"].strip())
                request.session["employee_id"] = employee.id
                request.session["employee_name"] = employee.name
                return redirect("leads:dashboard")
    else:
        form = LoginForm()

    return render(request, "leads/login.html", {"form": form})


def logout_view(request):
    request.session.flush()
    return redirect("leads:login")


@employee_required
def dashboard(request):
    query = request.GET.get("q", "").strip()

    leads = Lead.objects.select_related("created_by").prefetch_related("history__employee")
    if query:
        leads = leads.filter(
            Q(name__icontains=query)
            | Q(phone__icontains=query)
            | Q(city__icontains=query)
            | Q(lead_id__icontains=query)
        )
    leads = list(leads)

    for lead in leads:
        history = list(lead.history.all())
        lead.hist_id = f"hist-{lead.lead_id}"
        lead.history_count = len(history)
        lead.latest_update = history[-1] if history else None
        lead.history_data = [
            {
                "text": h.text,
                "status": h.status,
                "who": h.employee.name if h.employee else "Employee",
                "time": timezone.localtime(h.created_at).strftime("%d %b, %I:%M %p"),
            }
            for h in history
        ]

    context = {
        "leads_active": [l for l in leads if l.status == Lead.STATUS_ACTIVE],
        "leads_booked": [l for l in leads if l.status == Lead.STATUS_BOOKED],
        "leads_lost": [l for l in leads if l.status == Lead.STATUS_LOST],
        "total": len(leads),
        "employee_name": request.session.get("employee_name"),
        "query": query,
        "lead_form": LeadForm(),
        "update_form": UpdateForm(),
        "status_choices": Lead.STATUS_CHOICES,
    }
    return render(request, "leads/leads_dashboard.html", context)


@employee_required
@require_POST
def add_lead(request):
    form = LeadForm(request.POST)
    if form.is_valid():
        employee = Employee.objects.filter(id=request.session["employee_id"]).first()
        lead = form.save(commit=False)
        lead.created_by = employee
        lead.save()
        StatusUpdate.objects.create(
            lead=lead,
            text=(
                f"Naya user aaya — {lead.city} me room chahiye (₹{lead.budget})"
                + (f" · {lead.note}" if lead.note else "")
            ),
            status=Lead.STATUS_ACTIVE,
            employee=employee,
        )
        messages.success(request, "Naya lead add ho gaya")
    else:
        messages.error(request, "Form me kuch error hai — Naam aur Phone zaroori hain")
    return redirect("leads:dashboard")


@employee_required
@require_POST
def edit_lead(request, lead_id):
    lead = get_object_or_404(Lead, lead_id=lead_id)
    form = LeadForm(request.POST, instance=lead)
    if form.is_valid():
        form.save()
        messages.success(request, "Lead update ho gaya")
    else:
        messages.error(request, "Edit save nahi hua — fields check karein")
    return redirect("leads:dashboard")


@employee_required
@require_POST
def delete_lead(request, lead_id):
    lead = get_object_or_404(Lead, lead_id=lead_id)
    lead.delete()
    messages.success(request, "Lead delete ho gaya")
    return redirect("leads:dashboard")


@employee_required
@require_POST
def set_status(request, lead_id):
    lead = get_object_or_404(Lead, lead_id=lead_id)
    status = request.POST.get("status")
    if status not in dict(Lead.STATUS_CHOICES):
        messages.error(request, "Invalid status")
        return redirect("leads:dashboard")

    employee = Employee.objects.filter(id=request.session["employee_id"]).first()
    lead.status = status
    lead.save(update_fields=["status", "updated_at"])
    StatusUpdate.objects.create(
        lead=lead,
        text=f"{employee.name if employee else 'Employee'} ne status {lead.get_status_display()} kar diya",
        status=status,
        employee=employee,
    )
    messages.success(request, f"Status update: {lead.get_status_display()}")
    return redirect("leads:dashboard")


@employee_required
@require_POST
def add_update(request, lead_id):
    lead = get_object_or_404(Lead, lead_id=lead_id)
    form = UpdateForm(request.POST)
    if form.is_valid():
        employee = Employee.objects.filter(id=request.session["employee_id"]).first()
        new_status = form.cleaned_data.get("status") or lead.status
        if new_status != lead.status:
            lead.status = new_status
            lead.save(update_fields=["status", "updated_at"])
        StatusUpdate.objects.create(
            lead=lead,
            text=form.cleaned_data["text"],
            status=new_status,
            employee=employee,
        )
        messages.success(request, "Update add ho gaya")
    else:
        messages.error(request, "Update text likhna zaroori hai")
    return redirect("leads:dashboard")