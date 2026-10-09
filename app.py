import os
import re
import uuid
from flask import Flask, render_template, request, jsonify
import boto3
import pymysql
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

app = Flask(__name__)

# Allowed file extensions & input validation patterns
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
EMAIL_REGEX = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

VALID_COURSES = {
    "Computer Science & Engineering",
    "Electronics & Communication Engineering",
    "Electrical & Electronics Engineering",
    "Mechanical Engineering",
    "Civil Engineering",
    "Information Technology"
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    db_host = os.environ.get('DB_HOST')
    db_port = int(os.environ.get('DB_PORT', 3306))
    db_user = os.environ.get('DB_USER')
    db_password = os.environ.get('DB_PASSWORD')
    db_name = os.environ.get('DB_NAME', 'studentdb')

    if not db_host or not db_user:
        raise ValueError("Database configuration (DB_HOST, DB_USER) missing in environment variables.")

    return pymysql.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password or '',
        database=db_name,
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=5
    )

def get_s3_client():
    aws_region = os.environ.get('AWS_REGION', 'us-east-1')
    # boto3 automatically discovers credentials via environment variables,
    # ~/.aws/credentials, or EC2 IAM Instance Profile metadata.
    return boto3.client('s3', region_name=aws_region)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
              request.accept_mimetypes.best == 'application/json' or \
              request.is_json

    def respond(success, message, status_code=200):
        if is_ajax:
            return jsonify({'success': success, 'message': message}), status_code
        else:
            return f"<div style='font-family:sans-serif; padding:20px;'><h3 style='color:{'green' if success else 'red'};'>{'Success' if success else 'Error'}</h3><p>{message}</p><a href='/'>Go Back</a></div>", status_code

    # 1. Input Extraction
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    course = request.form.get('course', '').strip()
    photo = request.files.get('photo')

    # 2. Input Validation
    if not name:
        return respond(False, "Full Name is required.", 400)
    if not email or not re.match(EMAIL_REGEX, email):
        return respond(False, "Please enter a valid email address.", 400)
    if not course or course not in VALID_COURSES:
        return respond(False, "Please select a valid course from the dropdown.", 400)
    if not photo or photo.filename == '':
        return respond(False, "Student photo is required.", 400)
    if not allowed_file(photo.filename):
        return respond(False, "Invalid photo format. Only JPG, JPEG, and PNG images are allowed.", 400)

    # 3. Environment & AWS S3 Setup
    bucket_name = os.environ.get('S3_BUCKET_NAME')
    aws_region = os.environ.get('AWS_REGION', 'us-east-1')

    # 4. Unique Filename Generation
    file_ext = photo.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{file_ext}"

    s3_uploaded_key = None
    photo_url = None

    # 5. S3 Upload Handling
    if bucket_name:
        try:
            s3 = get_s3_client()
            s3.upload_fileobj(
                photo,
                bucket_name,
                unique_filename,
                ExtraArgs={'ContentType': photo.content_type or f'image/{file_ext}'}
            )
            s3_uploaded_key = unique_filename
            if aws_region == 'us-east-1':
                photo_url = f"https://{bucket_name}.s3.amazonaws.com/{unique_filename}"
            else:
                photo_url = f"https://{bucket_name}.s3.{aws_region}.amazonaws.com/{unique_filename}"
        except Exception as e:
            app.logger.error(f"S3 Upload Error: {str(e)}")
            return respond(False, "Failed to upload photo to S3. Please verify AWS S3 bucket and IAM permissions.", 500)
    else:
        # Fallback photo URL for local testing when S3 bucket is not configured
        photo_url = f"https://placeholder.local/photos/{unique_filename}"

    # 6. Database Insertion
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
        INSERT INTO students (name, email, course, photo_url)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (name, email, course, photo_url))
        conn.commit()

        return respond(True, "Registration Successful! Student details have been saved successfully.")

    except pymysql.Error as db_err:
        app.logger.error(f"Database Error: {str(db_err)}")
        # Cleanup uploaded S3 object if database insertion fails
        if s3_uploaded_key and bucket_name:
            try:
                s3 = get_s3_client()
                s3.delete_object(Bucket=bucket_name, Key=s3_uploaded_key)
                app.logger.info(f"Cleaned up orphaned S3 object: {s3_uploaded_key}")
            except Exception as cleanup_err:
                app.logger.error(f"Failed to cleanup orphaned S3 object: {str(cleanup_err)}")

        return respond(False, "Database error encountered during registration. Please verify RDS/MySQL connection.", 500)

    except ValueError as config_err:
        app.logger.error(f"Configuration Error: {str(config_err)}")
        return respond(False, f"System Configuration Error: {str(config_err)}", 500)

    except Exception as general_err:
        app.logger.error(f"Unexpected Error: {str(general_err)}")
        return respond(False, "An unexpected system error occurred.", 500)

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
