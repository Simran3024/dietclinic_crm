from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
import pymongo
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import os
import certifi
# ---------------- MongoDB Connection ----------------
# ---------------- MongoDB Connection ----------------
MONGO_URI = os.getenv("MONGO_URI")

try:
    client = pymongo.MongoClient(
        MONGO_URI,
        tls=True,
        tlsCAFile=certifi.where()
    )
    db = client["CRM"]
    users_collection = db["users"]
    leads_collection = db["leads"]
    customers_collection = db["customers"]
    plans_collection = db["plans"]
except Exception as e:
    print("❌ MongoDB connection failed:", e)
    traceback.print_exc()


# ---------------- SIGNUP ----------------
def signup_view(request):
    if request.method == "POST":
        try:
            username = request.POST.get("username")
            raw_password = request.POST.get("password")
            role = request.POST.get("role", "").upper()

            if not username or not raw_password:
                messages.error(request, "Username and password required.")
                return redirect("signup")

            if users_collection.find_one({"username": username}):
                messages.error(request, "Username already exists.")
                return redirect("signup")

            password = make_password(raw_password)

            users_collection.insert_one({
                "username": username,
                "password": password,
                "role": role
            })

            messages.success(request, "Signup successful! Please login.")
            return redirect("login")

        except Exception as e:
            print("❌ Signup error:", e)
            traceback.print_exc()
            messages.error(request, f"Signup failed: {str(e)}")
            return redirect("signup")

    return render(request, "accounts/signup.html")


# ---------------- LOGIN ----------------
def login_view(request):
    if request.method == 'POST':
        try:
            username = request.POST.get("username")
            raw_password = request.POST.get("password")
            role = request.POST.get("role", "").upper()

            user = users_collection.find_one({"username": username, "role": role})
            if user and check_password(raw_password, user["password"]):
                request.session["username"] = username
                request.session["role"] = role

                if role == 'ADMIN':
                    return redirect('admin_dashboard')
                elif role == 'COUNSELOR':
                    return redirect('counselor_dashboard')
                elif role == 'NUTRITIONIST':
                    return redirect('nutritionist_dashboard')

            messages.error(request, "Invalid username, password, or role.")
        except Exception as e:
            print("❌ Login error:", e)
            traceback.print_exc()
            messages.error(request, f"Login failed: {str(e)}")

    return render(request, 'accounts/login.html')

# ---------------- LOGOUT ----------------
def logout_view(request):
    request.session.flush()
    return redirect('login')

# ---------------- DASHBOARDS ----------------
def admin_dashboard(request):
    if request.session.get("role") != "ADMIN":
        return redirect("login")
    reminders = renewal_reminders()
    return render(request, "users/admin_ui/dashboard.html", {"renewal_reminders": reminders})

def counselor_dashboard(request):
    if request.session.get("role") != "COUNSELOR":
        return redirect("login")
    return render(request, 'users/counselor_ui/dashboard.html')

def nutritionist_dashboard(request):
    if request.session.get("role") != "NUTRITIONIST":
        return redirect("login")
    return render(request, 'users/nutritionist_ui/dashboard.html')

# ---------------- Webhook to Receive Instagram DMs ----------------
@csrf_exempt
def instagram_webhook(request):
    """
    Facebook will POST Instagram DM events here.
    """
    if request.method == "GET":
        # Verification challenge
        challenge = request.GET.get("hub.challenge")
        verify_token = request.GET.get("hub.verify_token")
        if verify_token == "YOUR_VERIFY_TOKEN":
            return JsonResponse({"hub.challenge": challenge})
        return JsonResponse({"status": "Invalid verify token"}, status=400)

    elif request.method == "POST":
        data = json.loads(request.body)
        for entry in data.get("entry", []):
            for msg in entry.get("messaging", []):
                sender_id = msg["sender"]["id"]
                message_text = msg["message"].get("text", "")
                timestamp = datetime.fromtimestamp(msg["timestamp"] / 1000)

                username = sender_id  # Fallback if IG username not provided
                if leads_collection.find_one({"instagram_username": username}):
                    continue  # Skip duplicates

                lead_doc = {
                    "name": username,
                    "instagram_username": username,
                    "contact": None,
                    "message": message_text,
                    "status": "NEW",
                    "assigned_to": None,
                    "source": "Instagram DM",
                    "created_time": timestamp.strftime("%Y-%m-%d %H:%M:%S")
                }
                leads_collection.insert_one(lead_doc)
        return JsonResponse({"status": "success"})

# ---------------- Leads Management ----------------
def leads_management(request):
    if request.session.get("role") != "ADMIN":
        return redirect("login")

    leads = list(leads_collection.find())
    for lead in leads:
        lead["id"] = str(lead["_id"])

    counselors = list(users_collection.find({"role": "COUNSELOR"}))
    nutritionists = list(users_collection.find({"role": "NUTRITIONIST"}))

    return render(request, "users/admin_ui/leads.html", {
        "leads": leads,
        "counselors": counselors,
        "nutritionists": nutritionists
    })

# ---------------- Update Lead Status ----------------
def update_lead_status(request, lead_id):
    if request.session.get("role") != "ADMIN":
        return redirect("login")

    new_status = request.POST.get("status")
    leads_collection.update_one(
        {"_id": pymongo.ObjectId(lead_id)},
        {"$set": {"status": new_status}}
    )
    messages.success(request, "Lead status updated.")
    return redirect("leads_management")

# ---------------- Assign Lead ----------------
def assign_lead(request, lead_id):
    if request.session.get("role") != "ADMIN":
        return redirect("login")

    assigned_to = request.POST.get("assigned_to")
    leads_collection.update_one(
        {"_id": pymongo.ObjectId(lead_id)},
        {"$set": {"assigned_to": assigned_to}}
    )
    messages.success(request, "Lead assigned successfully.")
    return redirect("leads_management")

# ---------------- Convert Lead to Customer ----------------
def convert_lead_to_customer(request, lead_id):
    if request.session.get("role") != "ADMIN":
        return redirect("login")

    lead = leads_collection.find_one({"_id": pymongo.ObjectId(lead_id)})
    if not lead:
        messages.error(request, "Lead not found.")
        return redirect("leads_management")

    if request.method == "POST":
        full_name = request.POST.get("full_name")
        age = int(request.POST.get("age"))
        weight = float(request.POST.get("weight"))
        plan_type = request.POST.get("plan_type")
        fees_status = request.POST.get("fees_status")
        joining_date = request.POST.get("joining_date")
        renewal_date = request.POST.get("renewal_date")

        customers_collection.insert_one({
            "full_name": full_name,
            "instagram_username": lead.get("instagram_username"),
            "contact": lead.get("contact"),
            "age": age,
            "weight": weight,
            "plan_type": plan_type,
            "fees_status": fees_status,
            "joining_date": joining_date,
            "renewal_date": renewal_date,
            "progress": [],
            "history": [{"plan": plan_type, "start": joining_date, "end": renewal_date, "status": fees_status}]
        })

        leads_collection.update_one(
            {"_id": pymongo.ObjectId(lead_id)},
            {"$set": {"status": "CONVERTED"}}
        )
        messages.success(request, "Lead converted to customer successfully!")
        return redirect("customers_management")

    return render(request, "users/admin_ui/convert_lead.html", {"lead": lead})

# ---------------- Customers Management ----------------
def customers_management(request):
    if request.session.get("role") != "ADMIN":
        return redirect("login")

    customers = list(customers_collection.find())
    for c in customers:
        c["id"] = str(c["_id"])
    return render(request, "users/admin_ui/customers.html", {"customers": customers})

# ---------------- Renewal Reminder Check ----------------
def renewal_reminders():
    today = datetime.now().date()
    upcoming_customers = customers_collection.find({"renewal_date": {"$exists": True}})

    reminders = []
    for c in upcoming_customers:
        try:
            renewal_date = datetime.strptime(c["renewal_date"], "%Y-%m-%d").date()
            days_left = (renewal_date - today).days
            if days_left <= 7 and c.get("fees_status") != "PAID":
                reminders.append({
                    "customer": c["full_name"],
                    "contact": c["contact"],
                    "plan": c.get("plan_type", "N/A"),
                    "days_left": days_left,
                    "renewal_date": renewal_date.strftime("%Y-%m-%d")
                })
        except:
            continue
    return reminders

def plans_management(request):
    if request.session.get("role") != "ADMIN":
        return redirect("login")

    plans = list(plans_collection.find())
    for p in plans:
        p["id"] = str(p["_id"])

    return render(request, "users/admin_ui/plans.html", {"plans": plans})
