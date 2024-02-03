from flask import Flask, render_template, request, redirect, url_for, flash, jsonify,json
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
from flask_bcrypt import Bcrypt
from datetime import datetime  # Add this import
from pymysql.cursors import DictCursor  # Import DictCursor
from collections import Counter

from datetime import datetime





app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with your own secret key




bcrypt = Bcrypt(app)

# MySQL configurations
db_config = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': '1234',
    'database': 'hotel',
}

mysql = pymysql.connect(**db_config)

# Flask-Login configurations
login_manager = LoginManager(app)
login_manager.login_view = 'login'




class User(UserMixin):
    def __init__(self, user_id, full_name, email, is_admin=False):
        self.id = user_id
        self.full_name = full_name
        self.email = email



class Admin(UserMixin):
    def __init__(self, admin_id, username):
        self.id = admin_id
        self.username = username
        self.is_admin = True
@login_manager.user_loader
def load_user(user_id):
    cursor = mysql.cursor()

    # Check if the user is in the users table
    cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
    user_data = cursor.fetchone()

    if user_data:
        user = User(user_data[0], user_data[1], user_data[2])
        user.id = user_data[0]
        user.full_name = user_data[1]
        user.email = user_data[2]
        return user

    # Check if the user is in the admin table
    cursor.execute('SELECT * FROM admin WHERE id = %s', (user_id,))
    admin_data = cursor.fetchone()

    if admin_data:
        admin = Admin(admin_data[0], admin_data[1])
        admin.id = admin_data[0]
        admin.username = admin_data[1]
        # Add debug statement to check is_admin status
        print(f"Admin is_admin: {admin.is_admin}")

        return admin

    return None



@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = mysql.cursor()
        cursor.execute('SELECT * FROM admin WHERE username = %s', (username,))
        admin_data = cursor.fetchone()

        if admin_data and admin_data[2] == password:
            admin = Admin(admin_data[0], admin_data[1])
            admin.id = admin_data[0]
            login_user(admin)

            flash('Admin login successful! User ID: {}, is_admin: {}'.format(current_user.id, current_user.is_admin),
                  'success')

            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('mainadminlogin.html')


@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    # Fetch all bookings from the database
    with mysql.cursor(DictCursor) as cursor:
        cursor.execute("SELECT * FROM booking")
        bookings = cursor.fetchall()

    if bookings is None:
        flash('Failed to fetch booking data.', 'error')
        return redirect(url_for('login'))  # or another suitable redirect

    # Print details of each booking
    for booking in bookings:
        print(f"Booking ID: {booking['booking_id']}")
        print(f"User ID: {booking['user_id']}")
        print(f"Check-in Date: {booking['checkin_date']}")
        print(f"Check-out Date: {booking['checkout_date']}")
        print(f"Number of Guests: {booking['num_of_guests']}")
        print(f"Total Amount: {booking['total_amount']}")
        print(f"Payment Method: {booking['payment_method']}")
        print(f"Booked Rooms: {booking['booked_rooms']}")

    return render_template('admin_dashboard.html', bookings=bookings)


@app.route('/admin/delete_booking/<int:booking_id>',methods=['GET', 'POST'])
@login_required
def delete_booking(booking_id):


    # Perform deletion logic here, for example:
    with mysql.cursor() as cursor:
        cursor.execute("DELETE FROM booking WHERE booking_id = %s", (booking_id,))
        mysql.commit()

    flash('Booking deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/edit_booking/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def edit_booking(booking_id):

    # Fetch the booking details from the database
    with mysql.cursor(DictCursor) as cursor:
        cursor.execute("SELECT * FROM booking WHERE booking_id = %s", (booking_id,))
        booking = cursor.fetchone()

    if request.method == 'POST':
        # Perform update logic here, for example:
        new_total_amount = request.form['total_amount']
        new_guests = request.form['guests']

        with mysql.cursor() as cursor:
            cursor.execute("UPDATE booking SET total_amount = %s, num_of_guests = %s WHERE booking_id = %s",
                           (new_total_amount, new_guests, booking_id))
            mysql.commit()

        flash('Booking updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('edit_booking.html', booking=booking)

# Add a new route for room availability
@app.route('/admin/room_availability')
@login_required
def room_availability():
    # Fetch all rooms from the database
    with mysql.cursor(DictCursor) as cursor:
        cursor.execute("SELECT * FROM rooms")
        rooms = cursor.fetchall()

    return render_template('roomadmin.html', rooms=rooms)

# Add a new route for the user dashboard
@app.route('/admin/user_dashboard')
@login_required
def user_dashboard():
    # Fetch all users from the database
    with mysql.cursor(DictCursor) as cursor:
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()

    return render_template('user_dashboard.html', users=users)



# Add route for adding a new room
@app.route('/admin/add_room', methods=['GET', 'POST'])
@login_required
def add_room():
    if request.method == 'POST':
        # Get room details from the form
        room_name = request.form['name']
        room_price = request.form['price']
        room_availability = request.form['availability']
        capacity = request.form['capacity']
        # Assuming you're getting the image path from the form
        image_path_value = request.form.get('image_path', '')  # Provide a default value if the field is not present
        # Insert the new room into the database
        with mysql.cursor() as cursor:
            cursor.execute("INSERT INTO rooms (room_name, price, availability, guest_capacity,image_path) VALUES (%s, %s, %s, %s,%s)",
                           (room_name, room_price, room_availability, capacity,image_path_value))
            mysql.commit()

        flash('Room added successfully!', 'success')
        return redirect(url_for('room_availability'))

    return render_template('add_room.html')


# Add route for editing an existing room
@app.route('/admin/edit_room/<int:room_id>', methods=['GET', 'POST'])
@login_required
def edit_room(room_id):
    # Fetch the room details from the database
    with mysql.cursor(DictCursor) as cursor:
        cursor.execute("SELECT * FROM rooms WHERE room_id = %s", (room_id,))
        room = cursor.fetchone()

    if request.method == 'POST':
        # Update room details in the database
        new_name = request.form['name']
        new_price = request.form['price']
        new_availability = request.form['availability']
        new_capacity = request.form['capacity']


        with mysql.cursor() as cursor:
            cursor.execute("UPDATE rooms SET room_name = %s, price = %s , availability = %s , guest_capacity = %s WHERE room_id = %s  ", (new_name, new_price, new_availability,new_capacity,room_id))
            mysql.commit()

        flash('Room updated successfully!', 'success')
        return redirect(url_for('room_availability'))

    return render_template('edit_room.html', room=room)


# Add route for deleting a room
@app.route('/admin/delete_room/<int:room_id>')
@login_required
def delete_room(room_id):
    # Delete the room from the database
    with mysql.cursor() as cursor:
        cursor.execute("DELETE FROM rooms WHERE room_id = %s", (room_id,))
        mysql.commit()

    flash('Room deleted successfully!', 'success')
    return redirect(url_for('room_availability'))


@app.template_filter('str_to_datetime')
def str_to_datetime(date_str, format='%Y-%m-%d'):
    if not date_str:
        return None  # Return None if the date string is empty

    return datetime.strptime(date_str, format)

app.jinja_env.filters['str_to_datetime'] = str_to_datetime


@app.route('/')
def home():
    if current_user.is_authenticated:
        sign_in_out_text = 'Sign Out'
    else:
        sign_in_out_text = 'Sign In'

    return render_template('hotel1.html', sign_in_out_text=sign_in_out_text)





@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Check if the password and confirm_password match
        if password != confirm_password:
            flash('Password and Confirm Password do not match', 'error')
            return redirect(url_for('register'))

        # Hash the password using bcrypt
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        cursor = mysql.cursor()

        # Check if the email is already registered
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            flash('Email is already registered', 'error')
            return redirect(url_for('register'))

        # Insert the new user into the database
        cursor.execute('INSERT INTO users (full_name, email, password) VALUES (%s, %s, %s)',
                       (full_name, email, hashed_password))
        mysql.commit()

        flash('Registration successful', 'success')
        return redirect(url_for('login'))

    return render_template('mainregister.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.cursor()
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user_data = cursor.fetchone()

        if user_data and bcrypt.check_password_hash(user_data[3], password):
            user = User(user_data[0], user_data[1], user_data[2])
            user.id = user_data[0]
            login_user(user)
            flash('Login successful', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password', 'error')

    return render_template('mainlogin.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout successful', 'success')
    return redirect(url_for('home'))

@app.route('/get_user_data', methods=['GET'])
@login_required
def get_user_data():
    user_data = {
        'full_name': current_user.full_name,
        'email': current_user.email
    }
    return jsonify(user_data)

from flask import session




@app.route('/booking', methods=['GET', 'POST'])
@login_required
def booking():
    if request.method == 'POST':
        try:
            # Get data from the form
            checkin_date_str = request.form['checkin_date']
            checkout_date_str = request.form['checkout_date']
            guest_name = request.form['guest_name']
            guest_count = request.form['num_of_guests']
            book_for_self = 'book_for_self' in request.form

            # Validate date format
            checkin_date = datetime.strptime(checkin_date_str, '%Y-%m-%d').date()
            checkout_date = datetime.strptime(checkout_date_str, '%Y-%m-%d').date()

            # Perform validation checks


            # Save booking details in session
            session['booking_details'] = {
                'checkin_date': checkin_date_str,
                'checkout_date': checkout_date_str,
                'guest_name': guest_name,
                'num_of_guests': guest_count,
                'book_for_self': book_for_self
            }

            # Redirect to the selectroom route
            return redirect(url_for('selectroom'))

        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD.', 'error')
            return render_template('booking.html')

    # Render the booking form
    return render_template('mainbooking.html')

@app.route('/selectroom', methods=['GET', 'POST'])
@login_required
def selectroom():
    # Retrieve booking details from the session
    booking_details = session.get('booking_details')

    # Redirect to the booking route if booking details are not present
    if not booking_details:
        flash('Please complete the booking form first.', 'error')
        return redirect(url_for('booking'))

    checkin_date_str = booking_details['checkin_date']
    checkout_date_str = booking_details['checkout_date']
    guest_name = booking_details['guest_name']
    guest_count = int(booking_details['num_of_guests'])
    book_for_self = booking_details['book_for_self']

    # Fetch available rooms from the database
    cursor = mysql.cursor()
    cursor.execute('SELECT * FROM rooms WHERE availability > 0 LIMIT 15')

    columns = [col[0] for col in cursor.description]
    rooms = [dict(zip(columns, row)) for row in cursor.fetchall()]



    print("Rooms:", rooms)

    # Retrieve selected rooms from the session
    selected_rooms = session.get('selected_rooms', [])


    # Render the select room page
    return render_template('mainselectroom.html', rooms=rooms, checkin_date=checkin_date_str,
                           checkout_date=checkout_date_str, guest_name=guest_name,
                           book_for_self=book_for_self, guest_count=guest_count,
                           selected_rooms=selected_rooms)

@app.route('/overview', methods=['GET', 'POST'])
@login_required
def overview():
    # Retrieve user details from the session
    user_details = {
        'name': current_user.full_name,  # Assuming your User class has a full_name attribute
        'email': current_user.email
    }

    # Retrieve booking details from the session
    booking_details = session.get('booking_details', {})
    checkin_date = booking_details.get('checkin_date', '')
    checkout_date = booking_details.get('checkout_date', '')
    num_of_guests = booking_details.get('num_of_guests', 0)

    # Retrieve selected rooms from the form data and parse as JSON
    selected_rooms_str = request.form.get('selected_rooms', '[]')
    selected_rooms = json.loads(selected_rooms_str)

    # Retrieve total amount from the form data
    total_amount = float(request.form.get('total_amount', 0.0))

    # After calculating total_amount and selected_rooms
    session['selected_rooms'] = selected_rooms
    session['total_amount'] = total_amount

    # In the overview route
    app.logger.info(f"Booking Details in Session: {session.get('booking_details')}")
    app.logger.info(f"Selected Rooms in Session: {session.get('selected_rooms')}")
    app.logger.info(f"Total Amount in Session: {session.get('total_amount')}")

    # Render the 'overview.html' template with the obtained data
    return render_template('mainoverview.html',
                           user_details=user_details,
                           booking_details={
                               'checkin_date': checkin_date,
                               'checkout_date': checkout_date,
                               'num_of_guests': num_of_guests,
                           },
                           selected_rooms=selected_rooms,
                           total_amount=total_amount)
@app.route('/confirm_booking', methods=['POST'])
@login_required
def confirm_booking():
    try:
        # Retrieve user details from the session
        user_id = current_user.id

        # Retrieve booking details from the session
        booking_details = session.get('booking_details', {})
        checkin_date = datetime.strptime(booking_details.get('checkin_date', ''), '%Y-%m-%d')
        checkout_date = datetime.strptime(booking_details.get('checkout_date', ''), '%Y-%m-%d')
        num_of_guests = booking_details.get('num_of_guests', 0)

        # Retrieve selected rooms from the session
        selected_rooms = session.get('selected_rooms', [])

        # Retrieve total amount from the session
        total_amount = session.get('total_amount', 0)

        # Retrieve payment method from the form data
        payment_method = request.form.get('payment_method')

        app.logger.info(f"User ID: {user_id}")
        app.logger.info(f"Check-in Date: {checkin_date}")
        app.logger.info(f"Check-out Date: {checkout_date}")
        app.logger.info(f"Number of Guests: {num_of_guests}")
        app.logger.info(f"Selected Rooms: {selected_rooms}")
        app.logger.info(f"Total Amount: {total_amount}")
        app.logger.info(f"Payment Method: {payment_method}")

        # Decrement the availability of selected rooms by category
        with mysql.cursor() as cursor:
            sql = """
                INSERT INTO booking (user_id, checkin_date, checkout_date, num_of_guests, total_amount, payment_method, booked_rooms)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
            user_id, checkin_date, checkout_date, num_of_guests, total_amount, payment_method, str(selected_rooms)))
            # Get the last inserted booking ID
            # Get the last inserted booking ID
            booking_id = cursor.lastrowid

            # Decrement the availability of selected rooms by category

            for room in selected_rooms:
                category = room['name']
                count = room['count']

                # Check if enough rooms are available
                cursor.execute("SELECT availability FROM rooms WHERE room_name = %s", (category,))
                availability_before = cursor.fetchone()[0]

                if availability_before >= count:
                    # Update availability
                    sql = """
                       UPDATE rooms
                       SET availability = availability - %s
                       WHERE room_name = %s;
                    """
                    cursor.execute(sql, (count, category))
                    app.logger.info(f"Updating category: {category}, count: {count}")
                    app.logger.info(f"Rows affected: {cursor.rowcount}")
                    app.logger.info(f"Category {category} updated successfully!")

        # Commit the changes to the database
        mysql.commit()

        # Clear the session data
        session.pop('booking_details', None)
        session.pop('selected_rooms', None)
        session.pop('total_amount', None)

        flash('Booking confirmed successfully!', 'success')
        return redirect(url_for('login'))

    except Exception as e:
        app.logger.error(f"Error confirming booking: {e}")
        flash('An error occurred while confirming the booking. Please try again.', 'error')
        return redirect(url_for('overview'))

@app.route('/my_bookings')
@login_required
def my_bookings():
    try:
        user_id = current_user.id

        print(f"User ID: {user_id}")  # Debug statement

        with mysql.cursor(DictCursor) as cursor:
            # Set the row factory to DictCursor for fetching results as dictionaries
            cursor.row_factory = DictCursor

            # Retrieve all bookings for the current user
            sql = "SELECT * FROM booking WHERE user_id = %s"
            cursor.execute(sql, (user_id,))
            bookings = cursor.fetchall()

            print(f"Bookings: {bookings}")  # Debug statement

        if not bookings:
            print("No bookings found for the user")  # Debug statement

        booking_details_list = []
        for booking in bookings:
            booking_id = booking.get('booking_id')
            checkin_date = booking.get('checkin_date')
            checkout_date = booking.get('checkout_date')
            num_of_guests = booking.get('num_of_guests')
            selected_rooms = booking.get('selected_rooms')
            booked_rooms = booking.get('booked_rooms')
            total_amount = booking.get('total_amount')

            # Convert booked_rooms string to a list
            booked_rooms_list = eval(booked_rooms) if booked_rooms else []

            # Append the details to the list for rendering
            booking_details_list.append({
                'booking_id': booking_id,
                'checkin_date': checkin_date,
                'checkout_date': checkout_date,
                'num_of_guests': num_of_guests,
                'total_amount' : total_amount,
                'booked_rooms': booked_rooms_list
            })



        print("Reached the end of the function")  # Debug statement

        return render_template('main_my_bookings.html', booking_details_list=booking_details_list)

    except Exception as e:
        app.logger.error(f"Error fetching bookings: {e}")
        flash('An error occurred while fetching bookings. Please try again.', 'error')
        return redirect(url_for('overview'))


# Add a new route for editing a user
@app.route('/admin/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    # Fetch the user details from the database
    with mysql.cursor(DictCursor) as cursor:
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

    if request.method == 'POST':
        # Update user details in the database
        new_full_name = request.form['full_name']
        new_email = request.form['email']

        with mysql.cursor() as cursor:
            cursor.execute("UPDATE users SET full_name = %s, email = %s WHERE id = %s",
                           (new_full_name, new_email, user_id))
            mysql.commit()

        flash('User updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('edit_user.html', user=user)

# Add a new route for deleting a user
@app.route('/admin/delete_user/<int:user_id>')
@login_required
def delete_user(user_id):
    # Delete the user from the database
    with mysql.cursor() as cursor:
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        mysql.commit()

    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))



if __name__ == '__main__':
    app.run(debug=True)