# StudentHub - AWS Cloud Student Registration System

A production-ready Flask web application designed for deployment on AWS (EC2 + RDS MySQL + S3 with IAM Role authentication). This project provides a secure, modern, and responsive portal for student registration and photo management.

---

## 🌟 Features

- **Modern & Responsive UI**: Built with pure HTML5, CSS3, and ES6 JavaScript (No bloated frameworks). Features a 2-column layout on desktop, smooth animations, drag-and-drop photo upload, and instant thumbnail preview.
- **Database Security**: Zero hardcoded credentials. Connects dynamically to MySQL / Amazon RDS via environment variables (`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`). Uses request-level connection management to prevent thread deadlocks or stale connection drops under Gunicorn.
- **AWS S3 Photo Upload & IAM Authentication**: Uploads student photos directly to AWS S3. Automatically generates unique UUID-based filenames (`uuid4().hex`) to prevent file collisions or overwrites.
- **Zero AWS Secrets in Code**: Uses standard AWS SDK credential lookup (`boto3`). When deployed on AWS EC2, temporary credentials are automatically acquired from the attached **EC2 IAM Role** without storing AWS access keys.
- **Input Validation**: Server-side and client-side validation for mandatory fields, email formatting, course selection, and image file types (`.jpg`, `.jpeg`, `.png`).
- **Transaction Safety & S3 Rollback**: If a database error occurs after an S3 photo upload, the uploaded file is automatically cleaned up (deleted) from S3 to prevent orphaned files.

---

## 🏗️ Technology Stack

- **Backend**: Python 3.11/3.12, Flask, PyMySQL, boto3, python-dotenv
- **Frontend**: HTML5, CSS3 (CSS Variables, Flexbox, Grid), Vanilla JavaScript (Fetch API, FileReader API)
- **Database**: MySQL / Amazon RDS MySQL
- **Object Storage**: AWS Simple Storage Service (S3)
- **Application Server**: Gunicorn WSGI
- **Cloud Platform**: AWS EC2, AWS RDS, AWS S3, AWS IAM

---

## 📂 Project Structure

```text
reg/
├── app.py              # Main Flask application with secure DB & S3 logic
├── requirements.txt    # Python package dependencies
├── .env.example        # Environment variable template file
├── .gitignore          # Git exclusion rules (.env, __pycache__, etc.)
├── README.md           # Comprehensive project documentation
├── templates/
│   └── index.html      # Modern two-column registration portal template
├── static/
│   ├── css/
│   │   └── style.css   # Custom vanilla CSS styling
│   └── js/
│       └── script.js   # Client-side validation, preview, and fetch logic
├── Dockerfile          # Container specification
└── Jenkinsfile         # CI/CD pipeline script
```

---

## 🛠️ Database Setup

Create the database and the `students` table in your MySQL / Amazon RDS instance:

```sql
CREATE DATABASE IF NOT EXISTS studentdb;
USE studentdb;

CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    course VARCHAR(255) NOT NULL,
    photo_url VARCHAR(512) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## ⚙️ Environment Variables Setup

Copy `.env.example` to `.env` and populate your database and S3 details:

```bash
cp .env.example .env
```

### `.env` File Example:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=studentdb

S3_BUCKET_NAME=your-s3-bucket-name
AWS_REGION=us-east-1
```

> ⚠️ **SECURITY NOTICE**: NEVER commit `.env` or AWS Access Keys to version control. The `.gitignore` file is configured to exclude `.env` automatically.

---

## 🚀 How to Run Locally

1. **Clone & Navigate to Project Directory**:
   ```bash
   cd C:\Users\USER\Desktop\reg
   ```

2. **Create & Activate Virtual Environment**:
   ```bash
   python -m venv venv
   # On Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   # On Linux/macOS:
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch Application**:
   - **Development Server**:
     ```bash
     python app.py
     ```
   - **Gunicorn Production Server**:
     ```bash
     gunicorn -w 3 -b 0.0.0.0:5000 app:app
     ```

5. **Access Application**:
   Open browser at [http://localhost:5000](http://localhost:5000).

---

## 🧪 How to Test Locally

1. **Normal Registration**:
   - Enter a valid Name (e.g. `Jane Doe`).
   - Enter a valid Email (e.g. `jane.doe@university.edu`).
   - Select a Course (e.g. `Computer Science & Engineering`).
   - Choose a valid photo (`.jpg`, `.jpeg`, or `.png`).
   - Click **Register Student**. Verify the green success banner appears.

2. **Invalid Email Validation**:
   - Enter an invalid email format (e.g. `jane.doe@invalid`).
   - Click **Register Student**. Verify an error alert appears highlighting the invalid email requirement.

3. **Invalid File Format Validation**:
   - Attempt to upload a non-image file (e.g. `.pdf` or `.txt`).
   - Verify that an alert error blocks the upload before submission.

4. **Photo Preview & Replace**:
   - Select a valid `.jpg` or `.png` file. Observe instant preview thumbnail and filename display.
   - Click **Replace** button to swap images seamlessly.

5. **Database & S3 Verification**:
   - Check the `students` table in MySQL (`SELECT * FROM students;`). Confirm `name`, `email`, `course`, and `photo_url` are properly inserted.
   - If S3 is configured, verify that the photo is uploaded to your S3 bucket under a unique UUID key (e.g. `a1b2c3d4e5f6...png`).

---

## ☁️ AWS Deployment Architecture & IAM Setup

When deploying to AWS:

```text
[ Client Browser ]
        │
        ▼ (Port 80 / 5000)
┌─────────────────────────────────────────┐
│ EC2 Instance (Public Subnet)            │
│  - Runs Gunicorn (app:app)              │
│  - IAM Instance Profile Attached        │
└──────────┬────────────────────┬─────────┘
           │                    │
           ▼ (IAM Role Auth)    ▼ (MySQL Port 3306)
┌──────────────────────┐  ┌─────────────────────────────────┐
│ Amazon S3 Bucket     │  │ Amazon RDS MySQL                │
│ (Photo Objects)      │  │ (Private Subnet / Sec Group)    │
└──────────────────────┘  └─────────────────────────────────┘
```

1. **EC2 IAM Role**: Attach an IAM Role with `AmazonS3FullAccess` (or custom S3 policy allowing `s3:PutObject`, `s3:DeleteObject`) to the EC2 Instance. `boto3` in Python will automatically inherit permissions from the IAM Role metadata service. **No AWS credentials are stored in code or configuration files.**
2. **Security Groups**:
   - **EC2 Security Group**: Allow inbound HTTP (Port 80/5000) from anywhere (`0.0.0.0/0`).
   - **RDS Security Group**: Allow inbound MySQL (Port 3306) ONLY from the EC2 Security Group ID.
