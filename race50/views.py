import csv
import datetime
from django import template
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import render, HttpResponseRedirect, redirect
from django.urls import reverse
import io
import math

register = template.Library()
User = get_user_model()

from .models import Session, Lap

# Helper functions
def try_parse_int_positive(value):
    try:
        num = int(value)
        if num > 0:
            return True, num
        return False, None
    except ValueError:
        return False, None

def parse_date_safe(s: str):
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s.strip(), fmt).date()
        except Exception:
            pass
    return datetime.today().date()


# Create your views here.
def global_context(request):
    if request.user.is_authenticated:
        last_five = Session.objects.filter(user=request.user).order_by('-created_at')[:5]
        return {
            "sessions": last_five
        }
    else:
        last_five = Session.objects.none()
        return {
            "sessions": last_five
        }


def index(request):
    if request.user.is_authenticated:
        session = (Session.objects.filter(user=request.user).order_by('-created_at', '-pk').first())
        return render(request, "race50/index.html", {
            "session": session
        })
    else:
        return render(request, "race50/index.html")


@login_required
def upload(request):
    if request.method != "POST":
        return render(request, "race50/upload.html")
    csv_file = request.FILES.get('csv_file')
    if not csv_file:
        return render(request, "race50/upload.html", {"message": "No file uploaded."})
    if not csv_file.name.lower().endswith(".csv"):
        return render(request, "race50/upload.html", {"message": "Invalid file extension. File must be '.csv'."})
    if csv_file.size > 10 * 1024 * 1024:  # 10 MB
        return render(request, "race50/upload.html", {"message": "File too large (limit: 10MB)."})
    
    head = csv_file.file.read(4096)
    if b"\x00" in head:
        return render(request, "race50/upload.html", {"message": "File appears to be binary or corrupted."})
    csv_file.file.seek(0)

    text_stream = io.TextIOWrapper(csv_file.file, encoding="utf-8-sig", errors="replace", newline="")
    sample = text_stream.read(4096)
    text_stream.seek(0)

    sniffer = csv.Sniffer()
    try:
        dialect = sniffer.sniff(sample, delimiters=[",", ";", "\t"])
    except csv.Error:
        dialect = csv.excel
        dialect.delimiter = ","

    reader = csv.DictReader(text_stream, dialect=dialect)
    if not reader.fieldnames:
        return render(request, "race50/upload.html", {"message": "Missing or invalid header."})

    errors = []
    valid_rows = []
    row_count = 0

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

    for (idx, row) in enumerate(reader, start=2):
        row_count += 1

        require = [session_id, track, date, lapnum, laptime, s1time, s2time, s3time]
        if any(row.get(col, "").strip() == "" for col in require):
            errors.append(f"Row {idx}: missing required fields")
            continue

        ok_lap, lap = try_parse_int_positive(row[lapnum])
        ok_total, total = try_parse_int_positive(row[laptime])
        ok_s1, s1 = try_parse_int_positive(row[s1time])
        ok_s2, s2 = try_parse_int_positive(row[s2time])
        ok_s3, s3 = try_parse_int_positive(row[s3time])

        if not (ok_lap and ok_s1 and ok_s2 and ok_s3 and ok_total):
            errors.append(f"Row {idx}: values must be positive")
            continue

        # Range check (10s–5min)
        if not (10000 <= total <= 300000):
            errors.append(f"Row {idx}: LapTime_ms out of expected range ({total} ms)")
            continue

        # Consistency check (±2 ms)
        tolerance_ms = 2
        delta = abs((s1 + s2 + s3) - total)
        if delta > tolerance_ms:
            errors.append(f"Row {idx}: S1_ms+S2_ms+S3_ms != LapTime_ms (Δ={delta} ms)")
            continue

        # Session ID consistency
        sid = row[session_id].strip()
        if file_session_id is None:
            file_session_id = sid
        elif sid != file_session_id:
            errors.append(f"Row {idx}: inconsistent SessionID '{sid}' (expected '{file_session_id}')")
            continue

        valid_rows.append({
            "session_id": sid,
            "track": row[track].strip(),
            "date": row[date].strip(),
            "lap": lap,
            "s1_ms": s1,
            "s2_ms": s2,
            "s3_ms": s3,
            "total_ms": total,
            "notes": row.get(notes, "").strip(),
        })

    if not valid_rows:
        return render(request, "race50/upload.html", {
            "message": "No valid rows found in the CSV.",
            "errors": errors
        })

    lap_times = [r["total_ms"] for r in valid_rows]
    s1_times  = [r["s1_ms"]    for r in valid_rows]
    s2_times  = [r["s2_ms"]    for r in valid_rows]
    s3_times  = [r["s3_ms"]    for r in valid_rows]

    bestlap_ms = min(lap_times)
    worstlap_ms = max(lap_times)
    avg_lap_ms = sum(lap_times) / len(lap_times)
    bests1_ms, bests2_ms, bests3_ms = min(s1_times), min(s2_times), min(s3_times)
    tbl_ms = bests1_ms + bests2_ms + bests3_ms

    mean = avg_lap_ms
    variance = sum((t - mean) ** 2 for t in lap_times) / len(lap_times)
    stddev = math.sqrt(variance)
    consistency_percent = (1 - (stddev / mean)) * 100

    best_row = min(valid_rows, key=lambda r: r["total_ms"])
    best_lap_number = best_row["lap"]

    summary = {
        "laps_count": len(valid_rows),
        "best_lap_ms": bestlap_ms,
        "best_lap_number": best_lap_number,
        "worst_lap_ms": worstlap_ms,
        "avg_lap_ms": avg_lap_ms,
        "tbl_ms": tbl_ms,
        "consistency_percent": consistency_percent,
        "best_s1_ms": bests1_ms,
        "best_s2_ms": bests2_ms,
        "best_s3_ms": bests3_ms
    }

    # local parse (uses your 'import datetime' module)
    def _parse_date_local(s):
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
            try:
                return datetime.datetime.strptime(s.strip(), fmt).date()
            except Exception:
                pass
        return datetime.date.today()

    first = valid_rows[0]
    parsed_date = _parse_date_local(first["date"])

    with transaction.atomic():
        session_obj = Session.objects.create(
            user=request.user,
            external_id=file_session_id,
            track=first["track"],
            date=parsed_date,
            laps_count=summary["laps_count"],
            best_lap_ms=summary["best_lap_ms"],
            best_lap_number=summary["best_lap_number"],
            worst_lap_ms=summary["worst_lap_ms"],
            avg_lap_ms=int(round(summary["avg_lap_ms"])),
            tbl_ms=summary["tbl_ms"],
            consistency_percent=summary["consistency_percent"],
            notes="",
        )
        Lap.objects.bulk_create([
            Lap(
                session=session_obj,
                lap=r["lap"],
                s1_ms=r["s1_ms"],
                s2_ms=r["s2_ms"],
                s3_ms=r["s3_ms"],
                total_ms=r["total_ms"],
                notes=r.get("notes", ""),
            )
            for r in valid_rows
        ])
    return redirect("session", session_id=session_obj.id)


@login_required
def session(request, session_id):
    session = (Session.objects.get(user=request.user, id=session_id))
    laps = (Lap.objects.filter(session=session))
    posibilities = (Session.objects.filter(user=request.user, track=session.track).exclude(id=session_id))

    if request.method == "POST":
        selected_option_id = request.POST.get("selectedOption")
        if selected_option_id:
            url = f"{reverse('session', args=[session.id])}?compare={selected_option_id}"
            return redirect(url)
        
    compare_id = request.GET.get("compare")
    if compare_id:
        compare = (Session.objects.get(user=request.user, id=compare_id))
        if compare:
            compare_laps = (Lap.objects.filter(session=compare))
    else:
        compare = None
        compare_laps = None
    return render(request, "race50/session.html", {
        "session": session,
        "laps": laps,
        "posibilities": posibilities,
        "compare": compare,
        "compare_laps": compare_laps
    })


@login_required
def sessions(request):
    sessions = (Session.objects.filter(user=request.user))

    return render(request, "race50/sessions.html", {
        "sessions": sessions
    })


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


