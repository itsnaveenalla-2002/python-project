from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User as AdminUser
from .models import User, Slot, Booking


# =========================
# BASIC PAGES
# =========================

def home(request):
    return render(request, 'home.html')


def terms(request):
    return render(request, 'terms.html')


def privacy(request):
    return render(request, 'privacy.html')


# =========================
# AUTHENTICATION
# =========================

def register(request):
    if request.method == 'POST':
        name = request.POST['name']
        email = request.POST['email']
        password = request.POST['password']
        role = request.POST['role']

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists ❌")
            return redirect('register')

        User.objects.create(
            name=name,
            email=email,
            password=password,
            role=role
        )

        messages.success(request, "Registration successful ✅")
        return redirect('login')

    return render(request, 'register.html')


def login_view(request):
    if request.method == 'POST':

        username_or_email = request.POST['email'].strip()
        password = request.POST['password'].strip()

        # =========================
        # CUSTOM APP USERS
        # =========================
        custom_user = User.objects.filter(
            email=username_or_email
        ).first()

        if custom_user and custom_user.password == password:

            if custom_user.role == 'tutor' and not custom_user.is_approved:
                return render(request, 'login.html', {
                    'error': 'Waiting for Admin Approval ⏳'
                })

            request.session['user_id'] = custom_user.id
            request.session['role'] = custom_user.role
            request.session['name'] = custom_user.name

            return redirect('dashboard')

        # =========================
        # DJANGO ADMIN USERS
        # Example: naveen@75
        # =========================
        django_user = authenticate(
            request,
            username=username_or_email,
            password=password
        )

        if django_user:

            login(request, django_user)

            # Superuser → Django admin
            if django_user.is_superuser:
                return redirect('/admin/')

            # Normal Django user → your tutor dashboard
            request.session['user_id'] = django_user.id
            request.session['role'] = 'tutor'
            request.session['name'] = django_user.username

            return redirect('dashboard')

        return render(request, 'login.html', {
            'error': 'Invalid Credentials ❌'
        })

    return render(request, 'login.html')


def logout_view(request):
    request.session.flush()
    return redirect('home')


# =========================
# DASHBOARD
# =========================

def dashboard(request):
    if 'user_id' not in request.session:
        return redirect('login')

    role = request.session['role']

    if role == 'student':
        return render(request, 'student_dashboard.html')

    elif role == 'tutor':
        return render(request, 'tutor_dashboard.html')

    elif role == 'admin':
        return render(request, 'admin_dashboard.html')


# =========================
# ADMIN FEATURES
# =========================

def view_users(request):
    if request.session.get('role') != 'admin':
        return redirect('login')

    users = User.objects.all()
    return render(request, 'view_users.html', {'users': users})


def view_tutors(request):
    if request.session.get('role') != 'admin':
        return redirect('login')

    tutors = User.objects.filter(
        role='tutor',
        is_approved=False
    )

    return render(request, 'approve_tutors.html', {
        'tutors': tutors
    })


def approve_tutor(request, user_id):
    if request.session.get('role') != 'admin':
        return redirect('login')

    user = User.objects.get(id=user_id)
    user.is_approved = True
    user.save()

    return redirect('view_tutors')


def delete_user(request, user_id):
    if request.session.get('role') != 'admin':
        return redirect('login')

    user = User.objects.get(id=user_id)
    user.delete()

    return redirect('view_users')


def all_slots_admin(request):
    if request.session.get('role') != 'admin':
        return redirect('login')

    slots = Slot.objects.all()

    return render(request, 'all_slots_admin.html', {
        'slots': slots
    })


def all_bookings(request):
    if request.session.get('role') != 'admin':
        return redirect('login')

    bookings = Booking.objects.all()

    return render(request, 'all_bookings.html', {
        'bookings': bookings
    })


def admin_cancel_booking(request, booking_id):
    if request.session.get('role') != 'admin':
        return redirect('login')

    booking = Booking.objects.get(id=booking_id)

    slot = booking.slot
    slot.is_booked = False
    slot.save()

    booking.delete()

    return redirect('all_bookings')


def reassign_booking(request, booking_id):
    if request.session.get('role') != 'admin':
        return redirect('login')

    booking = Booking.objects.get(id=booking_id)

    if request.method == 'POST':
        new_slot_id = request.POST.get('slot_id')
        new_slot = Slot.objects.get(id=new_slot_id)

        old_slot = booking.slot
        old_slot.is_booked = False
        old_slot.save()

        booking.slot = new_slot
        booking.tutor = new_slot.tutor
        booking.save()

        new_slot.is_booked = True
        new_slot.save()

        return redirect('all_bookings')

    slots = Slot.objects.filter(is_booked=False)

    return render(request, 'reassign_booking.html', {
        'booking': booking,
        'slots': slots
    })


# =========================
# TUTOR FEATURES
# =========================

def create_slot(request):
    if request.session.get('role') != 'tutor':
        return redirect('login')

    if request.method == 'POST':
        tutor_id = request.session.get('user_id')
        date = request.POST.get('date')
        time = request.POST.get('time')

        Slot.objects.create(
            tutor_id=tutor_id,
            date=date,
            time=time
        )

        return redirect('my_slots')

    return render(request, 'create_slot.html')


def my_slots(request):
    if request.session.get('role') != 'tutor':
        return redirect('login')

    tutor_id = request.session.get('user_id')

    slots = Slot.objects.filter(
        tutor_id=tutor_id
    )

    return render(request, 'my_slots.html', {
        'slots': slots
    })


# =========================
# STUDENT FEATURES
# =========================

def all_slots(request):
    if request.session.get('role') != 'student':
        return redirect('login')

    slots = Slot.objects.filter(
        is_booked=False
    )

    return render(request, 'all_slots.html', {
        'slots': slots
    })


def book_slot(request, slot_id):
    if request.session.get('role') != 'student':
        return redirect('login')

    student_id = request.session.get('user_id')

    student = User.objects.get(id=student_id)
    slot = Slot.objects.get(id=slot_id)
    tutor = User.objects.get(id=slot.tutor_id)

    if slot.is_booked:
        return redirect('all_slots')

    Booking.objects.create(
        student=student,
        tutor=tutor,
        slot=slot,
        status='booked'
    )

    slot.is_booked = True
    slot.save()

    return redirect('all_slots')


def my_bookings(request):
    role = request.session.get('role')
    user_id = request.session.get('user_id')

    if role == 'student':
        bookings = Booking.objects.filter(student_id=user_id)

    elif role == 'tutor':
        bookings = Booking.objects.filter(tutor_id=user_id)

    else:
        return redirect('login')

    return render(request, 'my_bookings.html', {
        'bookings': bookings
    })


def cancel_booking(request, booking_id):
    if request.session.get('role') != 'student':
        return redirect('login')

    booking = Booking.objects.get(id=booking_id)

    slot = Slot.objects.get(id=booking.slot_id)

    slot.is_booked = False
    slot.save()

    booking.delete()

    return redirect('my_bookings')