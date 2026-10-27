from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .forms import UserLoginForm, UserProfileForm, UserRegistrationForm
from apps.workspaces.permissions import get_user_workspace


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Ensure primary workspace is created immediately
            get_user_workspace(user)
            login(request, user)
            messages.success(request, f"¡Bienvenido a Sign & Go, {user.get_short_name()}! Tu espacio ha sido configurado.")
            return redirect("dashboard:home")
    else:
        form = UserRegistrationForm()

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")

    if request.method == "POST":
        form = UserLoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Ensure workspace is ready
            get_user_workspace(user)
            messages.success(request, f"Sesión iniciada correctamente.")
            next_url = request.GET.get("next") or "dashboard:home"
            return redirect(next_url)
    else:
        form = UserLoginForm()

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.info(request, "Has cerrado sesión correctamente.")
    return redirect("accounts:login")


@login_required
def profile_view(request):
    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil actualizado con éxito.")
            return redirect("accounts:profile")
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, "accounts/profile.html", {"form": form})
