from django.contrib.auth import get_user_model, authenticate, login, logout
from django.db import IntegrityError
from django.shortcuts import render, HttpResponseRedirect
from django.urls import reverse

User = get_user_model()

# Create your views here.
def index(request):
    return render(request, "race50/index.html")


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "race50/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "race50/login.html")


def register_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure Username and Email are set
        if username == '':
            return render(request, "race50/register.html", {
                "message": "You must set a Username"
            })
        
        # Ensure password exists and matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password == '':
            return render(request, "race50/register.html", {
                "message": "You must set a Password"
            })
        else:
            if password != confirmation:
                return render(request, "race50/register.html", {
                    "message": "Passwords must match."
                })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "race50/register.html", {
                "message": f'An account with this username already exists, please login <a href="{reverse("login")}">here</a>'
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "race50/register.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


