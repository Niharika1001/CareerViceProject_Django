from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from .models import Profile, CareerSuggestion
from openai import OpenAI

# OpenAI client for career suggestions
client = OpenAI(api_key=settings.OPENAI_API_KEY, base_url="https://openrouter.ai/api/v1")
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Prgeofile  # adjust if your Profile model is in a different app

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
# @login_required
# def profile_view(request):
#     user = request.user
#     profile, created = Profile.objects.get_or_create(user=user)

#     if request.method == "POST":
#         user.username = request.POST.get("username")
#         user.email = request.POST.get("email")
#         password = request.POST.get("password")
#         if password:
#             user.set_password(password)
#             update_session_auth_hash(request, user)

#         profile.alt_email = request.POST.get("alt_email")
#         profile.mobile = request.POST.get("mobile")
#         profile.gender = request.POST.get("gender")
#         profile.nationality = request.POST.get("nationality")
#         profile.religion = request.POST.get("religion")
#         profile.citizenship = request.POST.get("citizenship")
#         profile.qualification = request.POST.get("qualification")
#         profile.location = request.POST.get("location")
#         profile.address = request.POST.get("address")
#         profile.pin_code = request.POST.get("pin_code")
#         profile.state = request.POST.get("state")
#         profile.country = request.POST.get("country")

#         user.save()
#         profile.save()
#         messages.success(request, "Profile updated successfully.")
#         return redirect("profile")

#     gender_choices = ["Male", "Female", "Other"]
#     return render(request, "profile.html", {"profile": profile, "gender_choices": gender_choices})



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
        if qualification == "10th":
            return render(request, "form_10.html")
        elif qualification == "12th":
            return render(request, "form_12.html")
        elif qualification == "grad":
            return render(request, "form_grad.html")
        elif qualification == "pg":
            return render(request, "form_pg.html")
    return redirect("qualification")

# 8. Submit Form & Get Suggestion
@csrf_exempt
@login_required
def submit_form(request):
    if request.method == "POST":
        data = request.POST.dict()

        interest = data.get("interests", "")
        field = data.get("stream") or data.get("domain") or data.get("specialization") or "career"

        prompt = f"""
        A student is interested in '{interest}' and has a background in '{field}'.
        Based on this, suggest 2-3 ideal career paths.
        Be specific and useful.
        """

        try:
            response = client.chat.completions.create(
                model="openai/gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful AI career advisor."},
                    {"role": "user", "content": prompt.strip()}
                ]
            )
            suggestion_text = response.choices[0].message.content.strip()

            CareerSuggestion.objects.create(user=request.user, input_data=data, suggestion=suggestion_text)

            return render(request, "result.html", {
                "suggestion": suggestion_text,
                "data": data
            })

        except Exception as e:
            return render(request, "result.html", {
                "suggestion": "AI suggestion failed. Please try again later.",
                "data": data,
                "error": str(e)
            })

    return redirect("qualification")

# 9. Previous Suggestions
@login_required
def suggestions_view(request):
    previous_suggestions = CareerSuggestion.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "suggestions.html", {"previous_suggestions": previous_suggestions})
# 10. Result View - View last suggestion
@login_required
def result_view(request):
    last_suggestion = CareerSuggestion.objects.filter(user=request.user).order_by('-created_at').first()

    if not last_suggestion:
        messages.warning(request, "No suggestion found.")
        return redirect('home')

    return render(request, 'result.html', {
        'suggestion': last_suggestion.suggestion,
        'data': last_suggestion.input_data
    })
