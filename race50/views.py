import csv
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.shortcuts import render, HttpResponseRedirect
from django.urls import reverse
import io

User = get_user_model()

# Helper functions
def try_parse_int_positive(value):
    try:
        num = int(value)
        if num > 0:
            return True, num
        return False, None
    except ValueError:
        return False, None


# Create your views here.
def index(request):
    return render(request, "race50/index.html")


@login_required
def upload(request):
    if request.method == "POST":
        # File upload check
        csv_file = request.FILES.get('csv_file')
        if not csv_file:
            return render(request, "race50/upload.html", {
                "message": "No file uploaded."
            })
        if not csv_file.name.endswith(".csv") == True:
            return render (request, "race50/upload.html", {
                "message": "Invalid file extension. File must be '.csv'"
            })
        if csv_file.size > 10 * 1024 * 1024:  # 10 MB
            return render (request, "race50/upload.html", {
                "message": "File too large (limit: 10MB)"
            })
        
        # Quick binary sanity check (optional)
        if b"\x00" in csv_file.file.read(4096):
            return render(request, "race50/upload.html")
        csv_file.file.seek(0)
        # Wrap bytes as text with UTF-8
        text_stream = io.TextIOWrapper(csv_file.file, encoding="utf-8-sig", errors="replace", newline="")
        # Read small sample
        sample = text_stream.read(4096)
        text_stream.seek(0)
        sniffer = csv.Sniffer()
        try:
            dialect = sniffer.sniff(sample, delimiters=[",", ";", "\t"])
        except csv.Error:
            dialect = csv.excel
            dialect.delimiter = ","
        # Read the text_stream following dialect and sample
        reader = csv.DictReader(text_stream, dialect=dialect)
        # Get header row
        fieldnames = reader.fieldnames

        if not fieldnames:
            return render(request, "race50/upload.html")
        
        row_count = 0
        for row in reader:
            row_count += 1
            print(row)

        # Dictionaries for results
        errors = []
        valid_rows = []

        # Keys for headers
        session_id = "SessionID"
        track = "Track"
        date = "Date"
        lapnum = "Lap"
        laptime = "LapTime_ms"
        s1time = "S1_ms"
        s2time = "S2_ms"
        s3time = "S3_ms"
        notes = "Notes"

        file_session_id = None

        print("Starting to read rows")
        for (idx, row) in enumerate(reader, start=2):
            require = [session_id, track, date, lapnum, laptime, s1time, s2time, s3time]
            if any(row.get(col, "").strip() == "" for col in require):
                errors.append(f"Row {idx}: missing required fields")
                continue

            ok_lap, lap = try_parse_int_positive(row[lapnum])
            print(ok_lap, lap)
            ok_total, total = try_parse_int_positive(row[laptime])
            ok_s1, s1 = try_parse_int_positive(row[s1time])
            ok_s2, s2 = try_parse_int_positive(row[s2time])
            ok_s3, s3 = try_parse_int_positive(row[s3time])

            if not (ok_lap and ok_s1 and ok_s2 and ok_s3 and ok_total):
                errors.append(f"Row {idx}: values must be positive")
                continue

        if row_count == 0:
            return render(request, "race50/upload.html", {"message": "CSV has a header but no data rows"})
        else:
            return render(request, "race50/upload.html", {"message": f"Parsed successfully with {row_count} rows"})     
    return render(request, "race50/upload.html")


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


