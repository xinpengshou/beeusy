from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
from datetime import date, datetime, time, timedelta
import json
import random
import string
import requests
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)  # This enables CORS for all routes

# MySQL configuration
db_config = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 's20050124',
    'database': 'beeusy',
    'cursorclass': pymysql.cursors.DictCursor
}

# Infobip configuration
INFOBIP_API_KEY = "eb25f7f6238cd080642926ab92f901fb-f5579e11-c197-4f87-a040-ca27adfe7104"
INFOBIP_BASE_URL = "https://e5e551.api.infobip.com"
INFOBIP_SENDER = "InfoSMS"  # Replace with your sender ID or phone number

# Create a connection to the database
def get_db_connection():
    return pymysql.connect(**db_config)

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        elif isinstance(obj, time):
            return obj.strftime('%H:%M:%S')
        elif isinstance(obj, timedelta):
            return str(obj)
        return super().default(obj)

app.json_encoder = CustomJSONEncoder

@app.route('/api/categories', methods=['GET'])
def get_categories():
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT id, name FROM service_categories')
            categories = cursor.fetchall()
    return jsonify({'categories': categories})

@app.route('/api/services', methods=['GET'])
def get_services():
    category_id = request.args.get('category_id')
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            if category_id:
                cursor.execute('SELECT * FROM services WHERE category_id = %s', (category_id,))
            else:
                cursor.execute('SELECT * FROM services')
            services = cursor.fetchall()
    return jsonify({'services': services})

@app.route('/api/bookings', methods=['POST'])
def create_booking():
    booking_data = request.json
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            try:
                # First, save or update the address
                cursor.execute('''
                    INSERT INTO user_addresses (user_id, address, postal_code, city, province)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    address = VALUES(address),
                    postal_code = VALUES(postal_code),
                    city = VALUES(city),
                    province = VALUES(province)
                ''', (
                    booking_data['user_id'],
                    booking_data['address'],
                    booking_data.get('postal_code', ''),
                    booking_data['city'],
                    booking_data['province']
                ))

                # Then, create the booking
                cursor.execute('''
                    INSERT INTO bookings (user_id, service_id, booking_date, booking_time)
                    VALUES (%s, %s, %s, %s)
                ''', (
                    booking_data['user_id'],
                    booking_data['service_id'],
                    booking_data['booking_date'],
                    booking_data['booking_time']
                ))

                conn.commit()
                new_booking_id = cursor.lastrowid

                # Fetch the created booking details
                cursor.execute('''
                    SELECT b.id, b.booking_date, b.booking_time, 
                           s.name AS service_name, c.name AS category_name,
                           ua.address, ua.city, ua.province, ua.postal_code
                    FROM bookings b
                    JOIN services s ON b.service_id = s.id
                    JOIN service_categories c ON s.category_id = c.id
                    JOIN user_addresses ua ON b.user_id = ua.user_id
                    WHERE b.id = %s
                ''', (new_booking_id,))
                new_booking = cursor.fetchone()

                # Convert timedelta to string if necessary
                if isinstance(new_booking['booking_time'], timedelta):
                    new_booking['booking_time'] = str(new_booking['booking_time'])

                return jsonify({
                    'message': 'Booking created successfully',
                    'booking': new_booking
                }), 201
            except pymysql.Error as err:
                conn.rollback()
                return jsonify({'error': f'Error creating booking: {err}'}), 500

@app.route('/api/bookings/<int:user_id>', methods=['GET'])
def get_user_bookings(user_id):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('''
                SELECT b.*, s.name AS service_name, c.name AS category_name
                FROM bookings b
                JOIN services s ON b.service_id = s.id
                JOIN service_categories c ON s.category_id = c.id
                WHERE b.user_id = %s
            ''', (user_id,))
            bookings = cursor.fetchall()
    return jsonify({'bookings': bookings})

@app.route('/api/promotions', methods=['GET'])
def get_promotions():
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM promotions WHERE valid_to >= CURDATE()')
            promotions = cursor.fetchall()
    return jsonify({'promotions': promotions})

@app.route('/api/user_promotions/<int:user_id>', methods=['GET'])
def get_user_promotions(user_id):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('''
                SELECT up.*, p.title, p.description, p.discount_percentage
                FROM user_promotions up
                JOIN promotions p ON up.promotion_id = p.id
                WHERE up.user_id = %s AND up.is_used = FALSE AND p.valid_to >= CURDATE()
            ''', (user_id,))
            user_promotions = cursor.fetchall()
    return jsonify({'user_promotions': user_promotions})

@app.route('/api/save_address', methods=['POST'])
def save_address():
    address_data = request.json
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute('''
                    INSERT INTO user_addresses (user_id, address, postal_code, city, province)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    address = VALUES(address),
                    postal_code = VALUES(postal_code),
                    city = VALUES(city),
                    province = VALUES(province)
                ''', (
                    address_data['user_id'],
                    address_data['address'],
                    address_data.get('postal_code', ''),
                    address_data['city'],
                    address_data['province']
                ))
                conn.commit()
                return jsonify({'message': 'Address saved successfully'}), 200
            except pymysql.Error as err:
                conn.rollback()
                return jsonify({'error': f'Error saving address: {err}'}), 500

# Add this new global dictionary to store verification codes
verification_codes = {}

@app.route('/api/send-verification-code', methods=['POST'])
def send_verification_code():
    data = request.json
    phone_number = data.get('phone_number')

    print(f"Received request to send verification code to: {phone_number}")

    if not phone_number:
        print("Error: Phone number is missing")
        return jsonify({'error': 'Phone number is required'}), 400

    # Generate a random 6-digit verification code
    verification_code = ''.join(random.choices(string.digits, k=6))

    try:
        # Send SMS using Infobip
        url = f"{INFOBIP_BASE_URL}/sms/2/text/advanced"
        headers = {
            "Authorization": f"App {INFOBIP_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {
            "messages": [
                {
                    "from": INFOBIP_SENDER,
                    "destinations": [{"to": phone_number}],
                    "text": f"Your verification code is: {verification_code}"
                }
            ]
        }

        print(f"Sending SMS request to Infobip: {url}")
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raise an exception for non-200 status codes

        print(f"SMS sent successfully. Response: {response.text}")

        # Store the verification code
        verification_codes[phone_number] = verification_code

        return jsonify({'message': 'Verification code sent successfully'}), 200
    except Exception as e:
        print(f"Error sending SMS: {str(e)}")
        return jsonify({'error': 'Failed to send verification code'}), 500

@app.route('/api/verify-code', methods=['POST'])
def verify_code():
    data = request.json
    phone_number = data.get('phone_number')
    user_code = data.get('verification_code')

    if not phone_number or not user_code:
        return jsonify({'error': 'Phone number and verification code are required'}), 400

    stored_code = verification_codes.get(phone_number)

    if not stored_code:
        return jsonify({'error': 'No verification code found for this phone number'}), 404

    if user_code == stored_code:
        # Remove the used verification code
        del verification_codes[phone_number]
        return jsonify({'message': 'Verification successful'}), 200
    else:
        return jsonify({'error': 'Invalid verification code'}), 400

@app.route('/api/login-or-register', methods=['POST'])
def login_or_register():
    data = request.json
    phone_number = data.get('phone_number')
    verification_code = data.get('verification_code')

    if not phone_number or not verification_code:
        return jsonify({'error': 'Phone number and verification code are required'}), 400

    stored_code = verification_codes.get(phone_number)

    if not stored_code or stored_code != verification_code:
        return jsonify({'error': 'Invalid verification code'}), 400

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # Check if user exists
            cursor.execute('SELECT * FROM users WHERE phone_number = %s', (phone_number,))
            user = cursor.fetchone()

            if user:
                # User exists, return login success
                return jsonify({'message': 'Login successful', 'user_id': user['id'], 'username': user['username']}), 200
            else:
                # User doesn't exist, create new user
                username = f"User{random.randint(1000, 9999)}"
                cursor.execute('INSERT INTO users (phone_number, username) VALUES (%s, %s)', (phone_number, username))
                conn.commit()
                new_user_id = cursor.lastrowid
                return jsonify({'message': 'Registration successful', 'user_id': new_user_id, 'username': username}), 201

    # Remove the used verification code
    del verification_codes[phone_number]

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create the upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/upload-avatar', methods=['POST'])
def upload_avatar():
    if 'avatar' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['avatar']
    user_id = request.form.get('user_id')
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Use user_id in the filename to make it unique
        filename = f"{user_id}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Update the user's avatar in the database
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('UPDATE users SET userAvatar = %s WHERE id = %s', (filename, user_id))
                conn.commit()
        
        # Return the URL of the uploaded avatar
        avatar_url = f"/uploads/{filename}"
        return jsonify({'message': 'Avatar uploaded successfully', 'avatar_url': avatar_url}), 200
    
    return jsonify({'error': 'File type not allowed'}), 400

# Add this new route to check the server status
@app.route('/api/status', methods=['GET'])
def server_status():
    return jsonify({'status': 'Server is running'}), 200

if __name__ == '__main__':
    # Remove this line as we'll be using Gunicorn
    # app.run(debug=True, host='0.0.0.0', port=5000)
    pass
