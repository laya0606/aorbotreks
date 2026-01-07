# Aorbo Treks Website

A Django-based website for Aorbo Treks, a platform connecting trekkers with local trek organizers.

## Project Overview

This website was converted from a static HTML/CSS/JS website to a Django-based web application. The frontend design has been preserved while the backend has been migrated to Django.

## Features

- Responsive design
- Contact form with database storage
- Admin interface for managing contacts
- Multiple pages including Home, About, Blogs, Safety, and Contact

## Tech Stack

- Django 4.2.23
- PostgreSQL (Supabase)
- HTML/CSS/JavaScript
- Bootstrap
- `django-axes` for rate limiting
- `bleach` for XSS sanitization
- `python-magic` for robust MIME type validation

## Setup Instructions

### Prerequisites

- Python 3.8+
- PostgreSQL (for production, e.g., Supabase)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd aorbo-website
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows
   .\venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the project root with the following variables:
   ```
   SECRET_KEY='your_django_secret_key'
   DJANGO_ALLOWED_HOSTS='localhost,127.0.0.1,yourdomain.com'
   DB_NAME='your_db_name'
   DB_USER='your_db_user'
   DB_PASSWORD='your_db_password'
   DB_HOST='your_db_host'
   DB_PORT='your_db_port'
   DEBUG='True' # Set to 'False' for production
   ```

5. Run migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. Create a superuser for the admin interface:
   ```bash
   python manage.py createsuperuser
   ```

7. Run the development server:
   ```bash
   python manage.py runserver
   ```

8. Access the website at `http://127.0.0.1:8000/`

## Project Structure

- `aorbo_project/`: Django project settings, URL configurations, and serializers.
- `treks_app/`: Main Django application containing models, views, forms, and templates specific to the trekking platform.
- `templates/`: HTML templates for various pages.
- `static/`: Static files (CSS, JS, images) served by Django.
- `media/`: User-uploaded media files (e.g., blog images, testimonial photos).
- `.env`: Environment variables for sensitive information and configuration.
- `requirements.txt`: Python dependencies for the project.
- `Procfile`: For deployment on platforms like Render.
- `render.yaml`: Render Blueprint for infrastructure as code deployment.

## Admin Interface

Access the admin interface at `http://localhost:8000/supersecretadmin/` using the superuser credentials you created.

## Security Enhancements

Following a recent security audit, the following enhancements have been implemented:

- **Django Version Upgrade**: Updated to Django 4.2.23 to incorporate the latest security patches.
- **Rate Limiting**: Implemented using `django-axes` to protect against brute-force attacks and excessive requests.
- **XSS Protection**: User-submitted content (e.g., testimonials) is now sanitized using `bleach` to prevent Cross-Site Scripting vulnerabilities.
- **Robust File Upload Validation**: Integrated `python-magic` for more secure MIME type validation of uploaded files, reducing the risk of malicious file uploads.
- **Security Headers**: Configured `SECURE_CONTENT_TYPE_NOSNIFF` and `REFERRER_POLICY` to enhance browser security.
- **Clickjacking Protection**: `X_FRAME_OPTIONS` is set to `DENY` to prevent the site from being embedded in iframes.

## Deployment

This project is configured for deployment on platforms like Render using `Procfile` and `render.yaml`.

### Render Deployment Steps

1. **Connect to Git Repository**: Link your Render account to your Git repository.
2. **Create a New Web Service**: Choose "Web Service" in Render.
3. **Configure Build and Start Commands**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn aorbo_project.wsgi:application --log-file -`
4. **Environment Variables**: Add the environment variables defined in your `.env` file to Render's environment settings.
5. **Database**: Configure a PostgreSQL database on Render and link it to your web service.
6. **Static Files**: Ensure WhiteNoise is correctly configured in `aorbo_project/settings.py` for serving static files in production.

## Contact

For any inquiries, please contact:
- Email: info@aorbotreks.com
- Phone: +91 939 809 3503
# aorbotreksweb
