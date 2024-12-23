# Personalized Dictionary #

## Overview ##
Personalized Dictionary is a Django-based web application designed to help users build, manage,
and expand their vocabulary through a customized dictionary.

## Features ##

### User Management ###
- User registration and authentication.
- Email verification.
- Password reset.
- Personalized dashboard for each user.
- Manage user profiles with support for profile pictures.
- In DRF (Django Rest Framework), JWT is used for authentication.

### Dictionary Organization ###
- Organize vocabulary in custom folders (e.g., by books, topics, etc.)
- Create multiple dictionaries within each folder (e.g., each chapter vocabulary inside a book folder, etc.)

### Word Entry Management ###
- Add new words with their contexts.
- Enter word, target languages, and get auto-generated translations with example sentences 
using OpenAI API.
- Add custom meanings and personal example sentences to the generated context.
- Add notes (e.g., grammar points, collocations, etc.).
- Supports image attachment.

### Study Tools ###
- Convert dictionaries or dictionary folders to flashcard sets.
- Export dictionaries or dictionary folders as PDF files for offline use. 

## Search & Filter ###
- Comprehensive search through the database, including entries created by all users.
- Comprehensive search through personal dictionaries and dictionary folders.
- Filter dictionary folders by language.
- Sort entries inside the dictionary.

### Leaderboard ###
- **Overall statistics**:
    - Top five users with the highest number of dictionary entries.
    - Top five users with the highest number of user-generated example sentences.
    - Top five users with the longest ongoing streak in days.
- **Weekly statistics**:
    - Top five users with the highest number of weekly dictionary entries.
    - Top five users with the highest number of weekly user-generated example sentences.
    - Weekly statistics and streaks are automatically reset by using Celery.


## Technology Stack ##
- **Backend**:
    - Django (Web Framework)
    - Django Rest Framework (API)
    - SQLite (Database)
    - OpenAI API, model GPT-4o (Translation and example generation)
    - Django Weasyprint for PDF generation
    - DRF Spectacular (For API documentation)

- **Frontend**:
    - Django Templates
    - JavaScript


## Installation ##
1. Clone the repository
```bash
git clone https://github.com/NunuAbuashvili/personalized-dictionary.git
```

2. Set up virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Create .env file with required variables:
```
SECRET_KEY=
EMAIL_HOST=
EMAIL_PORT=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
OPEN_API_KEY=
```

5. Run migrations
```bash
python manage.py migrate
```

6. Create a superuser
```bash
python manage.py createsuperuser
```

7. Start development server
```bash
python manage.py runserver
```

## API Documentation ##

### Registration & Authentication ##
- `POST /api/account/signup/`: User registration
- `GET /api/account/verify-email/`: Verify user through email
- `POST /api/account/reset-password-request`: Request password reset
- `POST /api/account/reset-password`: Reset password
- `POST /api/users/token/refresh/`: Refresh JWT token
- `POST /api/users/password-reset/`: Request password reset
- `POST /api/users/password-reset-confirm/<uidb64>/<token>/`: Confirm password reset

POST /api/auth/register/: User registration
POST /api/auth/login/: User login
POST /api/auth/logout/: User logout

Languages

GET /api/languages/: List all available languages
POST /api/languages/: Create a new language category
GET /api/languages/{id}/: Retrieve a specific language category

Folders

GET /api/folders/: List all folders
POST /api/folders/: Create a new folder
GET /api/folders/{id}/: Retrieve a specific folder
PUT /api/folders/{id}/: Update a folder
DELETE /api/folders/{id}/: Delete a folder

Dictionaries

GET /api/dictionaries/: List all dictionaries
POST /api/dictionaries/: Create a new dictionary
GET /api/dictionaries/{id}/: Retrieve a specific dictionary
PUT /api/dictionaries/{id}/: Update a dictionary
DELETE /api/dictionaries/{id}/: Delete a dictionary

Words

GET /api/words/: List all words
POST /api/words/: Create a new word entry
GET /api/words/{id}/: Retrieve a specific word
PUT /api/words/{id}/: Update a word
DELETE /api/words/{id}/: Delete a word
POST /api/words/generate/: Generate translations and examples

Contributing

Fork the repository
Create a feature branch: git checkout -b feature-name
Commit your changes: git commit -am 'Add new feature'
Push to the branch: git push origin feature-name
Submit a pull request

License
This project is licensed under the MIT License - see the LICENSE file for details.
Acknowledgments

OpenAI for providing the API for translations and example generation
Django and Django REST Framework communities for excellent documentation and support