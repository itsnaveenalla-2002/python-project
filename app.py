from flask import Flask
from models import get_db_connection, init_db
from flask import request, redirect, session,render_template,flash
app = Flask(__name__)
app.secret_key = "supersecretkey123"
init_db()

@app.route('/')
def home():
    return "Tutor Booking System Running 🚀"

# ✅ Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO users (name, email, password, role)
                VALUES (?, ?, ?, ?)
            ''', (name, email, password, role))

            conn.commit()

            # ✅ Flash success message
            flash("Registration successful! Please login ✅")
           

            return redirect('/login')
        

        except:
            flash("Email already exists ❌")
            return redirect('/register')

        finally:
            conn.close()
        

    return render_template('register.html')

# ✅ Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM users WHERE email = ? AND password = ?
        ''', (email, password))

        user = cursor.fetchone()

        if user:
            # ✅ Store session
                session['user_id'] = user['id']
                session['role'] = user['role']
                session['name'] = user['name']

                if user['role'] == 'tutor':
                    cursor.execute('SELECT * FROM tutor_details WHERE user_id = ?', (user['id'],))
                tutor = cursor.fetchone()
                conn.close()

                if not  tutor:
                    conn.close()
                    return redirect('/tutor-form')
                

                if user['is_approved'] == 0:
                    conn.close()
                    return "Waiting for Admin Approval ⏳"
                

                conn.close()
                return redirect ('/dashboard')
           

        else:
            conn.close()
            return "Invalid Credentials ❌"


    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    role = session['role']

    if role == 'student':
        return render_template('student_dashboard.html')

    elif role == 'tutor':
        return render_template('tutor_dashboard.html')

    elif role == 'admin':
        return render_template('admin_dashboard.html')

    else:
        return "Invalid Role ❌"
    
# only for tutor
@app.route('/add-slot', methods=['GET', 'POST'])
def add_slot():
    if 'user_id' not in session:
        return redirect('/login')

    # ❗ Only tutor allowed
    if session['role'] != 'tutor':
        return "Access Denied ❌"

    if request.method == 'POST':
        date = request.form['date']
        time = request.form['time']
        tutor_id = session['user_id']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
        INSERT INTO slots (tutor_id, date, time)
        VALUES (?, ?, ?)
        ''', (tutor_id, date, time))

        conn.commit()
        conn.close()

        return "Slot Added Successfully ✅"

    return render_template('add_slot.html')

# view slots for tutor
@app.route('/my-slots')
def my_slots():
    if 'user_id' not in session:
        return redirect('/login')

    if session['role'] != 'tutor':
        return "Access Denied ❌"

    tutor_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    SELECT * FROM slots WHERE tutor_id = ?
    ''', (tutor_id,))

    slots = cursor.fetchall()
    conn.close()

    return render_template('view_slots.html', slots=slots)


# students all slots
@app.route('/all-slots')
def all_slots():
    if 'user_id' not in session:
        return redirect('/login')

    # ❗ Only student allowed
    if session['role'] not in ['student', 'admin']:
        return "Access Denied ❌"

    conn = get_db_connection()
    cursor = conn.cursor()


    cursor.execute('''
    SELECT 
    slots.id,
    slots.date,
    slots.time,
    users.name,
    tutor_details.subject,
    tutor_details.experience,
    tutor_details.qualification
    FROM slots
    JOIN users ON slots.tutor_id = users.id
    JOIN tutor_details ON users.id = tutor_details.user_id
    WHERE slots.is_booked = 0
    AND users.is_approved = 1
    ''')


    slots = cursor.fetchall()
    conn.close()

    return render_template('all_slots.html', slots=slots)


@app.route('/book/<int:slot_id>')
def book_slot(slot_id):
    if 'user_id' not in session:
        return redirect('/login')

    if session['role'] != 'student':
        return "Access Denied ❌"

    student_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    # 🔍 Get slot details
    cursor.execute('SELECT * FROM slots WHERE id = ?', (slot_id,))
    slot = cursor.fetchone()

    if slot is None:
        return "Slot not found ❌"

    # ❌ Prevent double booking
    if slot['is_booked'] == 1:
        return "Already booked ❌"

    # ✅ Insert booking
    cursor.execute('''
    INSERT INTO bookings (student_id, tutor_id, slot_id, status)
    VALUES (?, ?, ?, ?)
    ''', (student_id, slot['tutor_id'], slot_id, 'booked'))

    # ✅ Mark slot as booked
    cursor.execute('''
    UPDATE slots SET is_booked = 1 WHERE id = ?
    ''', (slot_id,))

    conn.commit()
    conn.close()

    return "Slot Booked Successfully ✅"



#cancel booking
@app.route('/cancel/<int:booking_id>')
def cancel_booking(booking_id):
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor()

    # 🔍 Get slot_id from booking
    cursor.execute('SELECT slot_id FROM bookings WHERE id = ?', (booking_id,))
    booking = cursor.fetchone()

    if booking:
        slot_id = booking['slot_id']

        # ✅ Make slot available again
        cursor.execute('''
        UPDATE slots SET is_booked = 0 WHERE id = ?
        ''', (slot_id,))

        # ✅ Update booking status
        cursor.execute('''
        UPDATE bookings SET status = 'cancelled' WHERE id = ?
        ''', (booking_id,))

        conn.commit()

    conn.close()

    return redirect('/my-bookings')

  
  
  #------------------------------------------------
  #admin
 #------------------------------------------------
# view all users

@app.route('/admin/users')
def view_users():
    if 'user_id' not in session:
        return redirect('/login')

    if session['role'] != 'admin':
        return "Access Denied ❌"

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()

    conn.close()

    return render_template('admin_users.html', users=users)

# approve tutor

@app.route('/admin/tutors')
def approve_tutors():
    if 'user_id' not in session:
        return redirect('/login')

    if session['role'] != 'admin':
        return "Access Denied ❌"

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    SELECT * FROM users WHERE role = 'tutor' AND is_approved = 0
    ''')

    tutors = cursor.fetchall()
    conn.close()

    return render_template('approve_tutors.html', tutors=tutors)

#tutor approved 

@app.route('/admin/approve/<int:user_id>')
def approve_user(user_id):
    if 'user_id' not in session:
        return redirect('/login')

    if session['role'] != 'admin':
        return "Access Denied ❌"

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    UPDATE users SET is_approved = 1 WHERE id = ?
    ''', (user_id,))

    conn.commit()
    conn.close()

    return redirect('/admin/tutors')

# my bookings

@app.route('/my-bookings')
def my_bookings():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor()

    if session['role'] == 'admin':
        cursor.execute('''
        SELECT bookings.*, slots.date, slots.time
        FROM bookings
        JOIN slots ON bookings.slot_id = slots.id
        ''')

    elif session['role'] == 'student':
        student_id = session['user_id']
        cursor.execute('''
        SELECT bookings.*, slots.date, slots.time
        FROM bookings
        JOIN slots ON bookings.slot_id = slots.id
        WHERE bookings.student_id = ?
        ''', (student_id,))

    else:
        return "Access Denied ❌"

    bookings = cursor.fetchall()
    conn.close()

    return render_template('bookings.html', bookings=bookings)

#register form for tutor

@app.route('/tutor-form', methods=['GET', 'POST'])
def form_tutor():
    
    if 'user_id' not in session:
        return redirect('/login')

    
    if session['role'] != 'tutor':
         return redirect('/dashboard')

    user_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    
    cursor.execute('SELECT * FROM tutor_details WHERE user_id = ?', (user_id,))
    existing = cursor.fetchone()

    if request.method == 'POST':
        subject = request.form['subject']
        experience = request.form['experience']
        qualification = request.form['qualification']

        if existing:
            conn.close()
            return "Already submitted ❌"

        cursor.execute('''
        INSERT INTO tutor_details (user_id, subject, experience, qualification)
        VALUES (?, ?, ?, ?)
        ''', (user_id, subject, experience, qualification))

        conn.commit()
        conn.close()

        return "Submitted. Wait for approval ⏳"

    conn.close()
    return render_template('tutor_form.html')
#profile
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor()
    user_id = session['user_id']

    # ✅ Update profile
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']

        cursor.execute('''
        UPDATE users SET name = ?, email = ? WHERE id = ?
        ''', (name, email, user_id))

        # ✅ If tutor → update tutor details also
        if session['role'] == 'tutor':
            subject = request.form['subject']
            experience = request.form['experience']
            qualification = request.form['qualification']

            cursor.execute('''
            UPDATE tutor_details
            SET subject = ?, experience = ?, qualification = ?
            WHERE user_id = ?
            ''', (subject, experience, qualification, user_id))

        conn.commit()

    # ✅ Fetch user data
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()

    # ✅ Fetch tutor details (only if tutor)
    tutor = None
    if session['role'] == 'tutor':
        cursor.execute('SELECT * FROM tutor_details WHERE user_id = ?', (user_id,))
        tutor = cursor.fetchone()

    conn.close()

    return render_template('profile.html', user=user, tutor=tutor)

@app.route('/tutors')
def view_tutors():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    SELECT users.name, tutor_details.subject, 
           tutor_details.experience, tutor_details.qualification
    FROM users
    JOIN tutor_details ON users.id = tutor_details.user_id
    WHERE users.role = 'tutor' AND users.is_approved = 1
    ''')

    tutors = cursor.fetchall()
    conn.close()

    return render_template('tutors.html', tutors=tutors)


@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully ✅")
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)

