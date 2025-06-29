from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import requests
import logging
from django.conf import settings
from .models import Profile, CareerSuggestion
from openai import OpenAI
from django.shortcuts import get_object_or_404


# OpenAI client for career suggestions
client = OpenAI(api_key=settings.OPENAI_API_KEY, base_url="https://openrouter.ai/api/v1")


# 1. Signup View
def signup_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if not username or not email or not password1 or not password2:
            messages.error(request, "All fields are required.")
            return redirect("signup")

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect("signup")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("signup")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect("signup")

        user = User.objects.create_user(username=username, email=email, password=password1)
        Profile.objects.create(user=user)
        messages.success(request, "Account created successfully. Please log in.")
        return redirect("login")

    return render(request, "signup.html")

# 2. Login View
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        if not username or not password:
            messages.error(request, "Please enter both username and password.")
            return redirect("login")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            messages.success(request, "Logged in successfully!")
            return redirect("home")
        else:
            messages.error(request, "Invalid username or password.")
            return redirect("login")

    return render(request, "login.html")


# 3. Logout View
@login_required
def logout_view(request):
    logout(request)
    return redirect("login")

# 4. Home View (with last suggestion)
@login_required
def home_view(request):
    last_suggestion = CareerSuggestion.objects.filter(user=request.user).order_by("-created_at").first()
    return render(request, "home.html", {"last_suggestion": last_suggestion})

# # 5. Profile View

@login_required
def profile_view(request):
    user = request.user
    profile = user.profile

    gender_choices = ["Male", "Female", "Other"]  # Ensure this matches your form

    if request.method == "POST":
        # Basic info
        user.username = request.POST.get("username")
        user.email = request.POST.get("email")

        # Profile info
        profile.alt_email = request.POST.get("alt_email")
        profile.mobile = request.POST.get("mobile")
        profile.gender = request.POST.get("gender")
        profile.religion = request.POST.get("religion")
        profile.nationality = request.POST.get("nationality")
        profile.citizenship = request.POST.get("citizenship")

        # Location info
        profile.qualifications = request.POST.get("qualifications") or ""
        profile.location = request.POST.get("location") or ""
        profile.state = request.POST.get("state") or ""
        profile.country = request.POST.get("country") or ""
        profile.pin_code = request.POST.get("pin_code") or ""
        profile.address = request.POST.get("address") or ""

        # Password change
        new_password = request.POST.get("password")
        if new_password:
            user.set_password(new_password)
            update_session_auth_hash(request, user)

        user.save()
        profile.save()
        messages.success(request, "Profile updated successfully!")
        return redirect("profile")

    return render(request, "profile.html", {
        "profile": profile,
        "gender_choices": gender_choices,
    })


# 7. Load Dynamic Form 
@csrf_exempt
@login_required
def load_form(request):
    if request.method == "POST":
        qualification = request.POST.get("qualification")

        interests = [
            "Technology", "Arts", "Science", "Sports", "Music", "Writing", "Design", "Business",
            "Healthcare", "Education", "Environment", "Social Work", "Finance", "Engineering"
        ]
        strengths = [
            "Leadership", "Communication", "Problem Solving", "Creativity", "Teamwork", "Analysis",
            "Organization", "Technical Skills", "Public Speaking", "Research", "Innovation", "Empathy"
        ]
        concerns = [
            "Public Speaking", "Job Security", "Work-life Balance", "Financial Stability", "Competition",
            "Technology Changes", "Networking", "Decision Making", "Time Management", "Stress"
        ]
        status_list = ["Completed", "Ongoing", "Discontinued"]
        stream_list = ["MPC", "BiPC", "MBiPC", "CEC", "MEC"]
        specialization_list = ["Engineering", "Medical", "Commerce", "Humanities"]

        if qualification == "10th":
            return render(request, "form_10.html", {
                "interests_list": interests,
                "strengths_list": strengths,
                "concerns_list": concerns
            })

        elif qualification == "12th":
            return render(request, "form_12.html", {
                "interests_list": interests,
                "strengths_list": strengths,
                "concerns_list": concerns,
                "status_list": status_list,
                "stream_list": stream_list,
                "specialization_list": specialization_list
            })

        elif qualification == "grad":
            specialization_list = [
                 "Engineering", "Medical", "Commerce", "Humanities",
                  "Law", "Banking & Finance", "Media & Journalism",
                   "Management", "Agriculture", "Design", "Social Sciences"
                 ]
            return render(request, "form_grad.html", {
        "interests_list": interests,
        "strengths_list": strengths,
        "concerns_list": concerns,
        "status_list": ["Completed", "Ongoing", "Discontinued"],
        "specialization_list": specialization_list
        })
        elif qualification == "pg":
            
            specialization_list = [
        "M.Tech / ME", "M.Sc", "M.Com", "MBA / PGDM", "MA (Arts, Humanities)",
        "LLM", "MCA", "M.Ed", "M.Pharma", "MSW", "MPH (Public Health)", "Others"
    ]
            return render(request, "form_pg.html", {
        "interests_list": interests,
        "strengths_list": strengths,
        "concerns_list": concerns,
        "status_list": ["Completed", "Ongoing", "Discontinued"],
        "specialization_list": specialization_list
    })

    return redirect("qualification")

# 8. Submit Form & Get Suggestion


logger = logging.getLogger(__name__)

@csrf_exempt
@login_required
def submit_form(request):
    if request.method == "POST":
        # Build form data dictionary manually
        data = {
            key: value for key, value in request.POST.items()
            if key not in ['csrfmiddlewaretoken', 'interests', 'strengths', 'concerns']
        }

        # Properly collect multi-value fields
        interests_list = request.POST.getlist('interests')
        strengths_list = request.POST.getlist('strengths')
        concerns_list = request.POST.getlist('concerns')

        # Store as comma-separated string
        interests = ", ".join([item.strip() for item in interests_list])
        strengths = ", ".join([item.strip() for item in strengths_list])
        concerns = ", ".join([item.strip() for item in concerns_list])

        # Add these cleaned multi-values to the main data dict
        data["interests"] = interests
        data["strengths"] = strengths
        data["concerns"] = concerns

        qualification = request.POST.get("qualification", "").lower()
        job_type = data.get("job_type", "")
        field = data.get("field_of_study", "")
        stream = data.get("stream", "")
        specialization = data.get("specialization", "")
        status = data.get("status", "")

        # Build dynamic prompt based on qualification
        if qualification == "10th":
            prompt = f"""
You are an expert career advisor. A 10th-grade student has the following:
- Interests: {interests}
- Strengths: {strengths}
- Concerns: {concerns}

Suggest exactly 5 career options that suit this profile. 
Format:

1. **<Career Title>** — One-line description.
2. ...
No intro or conclusion. Just clear, point-wise list with bolded titles.
"""
        elif qualification == "12th":
            prompt = f"""
You are an expert career advisor. A 12th-grade student has:
- Stream: {stream}
- Specialization: {specialization}
- Status: {status}
- Interests: {interests}
- Strengths: {strengths}
- Concerns: {concerns}

Suggest exactly 5 career paths that are most suitable.
Format:

1. **<Career Title>** — One-line description.
2. ...
Avoid long paragraphs. Keep output short, neat, and point-wise only.
"""
        elif qualification == "grad":
            prompt = f"""
A student has finished undergrad with:
- Specialization: {specialization}
- Interests: {interests}
- Strengths: {strengths}
- Concerns: {concerns}
- Preferred Job Type: {job_type}

Based on this, suggest exactly 5 career roles.
Use this format:

1. **<Career Title>** — One-line description.
2. ...
Output only the list. No extra explanation or paragraph.
"""
        elif qualification == "pg":
            prompt = f"""
This postgraduate student has:
- Specialization: {specialization}
- Interests: {interests}
- Strengths: {strengths}
- Concerns: {concerns}
- Preferred Job Type: {job_type}

Suggest exactly 5 advanced careers suited to them.

Format strictly:
1. **<Career Title>** — One-line description.
2. ...
Keep it minimal and easy to read.
"""
        else:
            prompt = f"""
A student with limited background shared:
- Interests: {interests}
- Strengths: {strengths}
- Concerns: {concerns}

Suggest exactly 5 suitable career paths.

Format:
1. **<Career Title>** — One-line description.
2. ...
Only list. No long texts or paragraphs.
"""

        try:
            headers = {
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "CareerVice"
            }

            json_data = {
                "model": "mistralai/mistral-7b-instruct",
                "messages": [
                    {"role": "system", "content": "You are a helpful AI career advisor."},
                    {"role": "user", "content": prompt.strip()}
                ]
            }

            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=json_data)
            response.raise_for_status()

            suggestion_text = response.json()["choices"][0]["message"]["content"].strip()

            # Save result
            suggestion_obj = CareerSuggestion.objects.create(
                user=request.user,
                input_data=data,
                suggestion=suggestion_text
            )

            return render(request, "result.html", {
                "suggestion": suggestion_text,
                "data": data,
                "generated_at": suggestion_obj.created_at,
                "last_suggestion": suggestion_obj,
            })

        except Exception as e:
            logger.error(f"AI Suggestion Error: {e}")
            messages.error(request, "AI suggestion failed. Please try again later.")
            return render(request, "result.html", {
                "suggestion": "No suggestion available due to an error.",
                "data": data,
                "generated_at": None,
            })

    return redirect("home")

# 9. Previous Suggestions
@login_required
def suggestions_view(request):
    previous_suggestions = CareerSuggestion.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "suggestions.html", {"previous_suggestions": previous_suggestions})


# View for the most recent suggestion
@login_required
def result_view(request):
    last_suggestion = CareerSuggestion.objects.filter(user=request.user).order_by('-created_at').first()

    if not last_suggestion:
        messages.warning(request, "No suggestion found.")
        return redirect('home')

    return render(request, 'result.html', {
        'suggestion': last_suggestion.suggestion,
        'data': last_suggestion.input_data,
        'generated_at': last_suggestion.created_at,  # consistent usage
    })

# View for a specific suggestion (View Full)
@login_required
def view_suggestion(request, id):
    suggestion = get_object_or_404(CareerSuggestion, id=id, user=request.user)

    return render(request, 'result.html', {
        'suggestion': suggestion.suggestion,
        'data': suggestion.input_data,
        'generated_at': suggestion.created_at,  # consistent usage
    })
