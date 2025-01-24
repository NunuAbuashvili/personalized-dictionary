# Personalized Dictionary #

## Overview ##
Personalized Dictionary is a Django-based web application designed to help users build, manage,
and expand their vocabulary through a customized dictionary.

![alt text](/media/project_screenshots/main.jpg)

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
- Select dictionary visibility (public/private).

![alt text](/media/project_screenshots/folders.jpg)

### Word Entry Management ###
- Add new words with their contexts.
- Enter word, target languages, and get auto-generated translations with example sentences 
using OpenAI API.
- Add custom meanings and personal example sentences to the generated context.
- Add notes (e.g., grammar points, collocations, etc.).
- Supports image attachment.

![alt text](/media/project_screenshots/entry%20detail%20one.jpg)
![alt text](/media/project_screenshots/entry%20detail%20two.jpg)

### Study Tools ###
- Convert dictionaries or dictionary folders to flashcard sets.
- Export dictionaries or dictionary folders as PDF files for offline use. 

![alt text](/media/project_screenshots/flashcards.jpg)

## Search & Filter ###
- Comprehensive search through the database, including entries created by all users.
- Comprehensive search through personal dictionaries and dictionary folders.
- Filter dictionary folders by language.
- Sort entries inside the dictionary.

![alt text](/media/project_screenshots/search%20results.jpg)

### Leaderboard ###
- **Overall statistics**:
    - Top five users with the highest number of dictionary entries.
    - Top five users with the highest number of user-generated example sentences.
    - Top five users with the longest ongoing streak in days.
- **Weekly statistics**:
    - Top five users with the highest number of weekly dictionary entries.
    - Top five users with the highest number of weekly user-generated example sentences.
    - Weekly statistics and streaks are automatically reset by using Celery.

![alt text](/media/project_screenshots/leaderboard.jpg)

### Access Control & Permissions ###

- **Public Access** 
  - View all public folders and dictionaries
  - Browse dictionary entries
  - Access the leaderboard
  - Search functionality for dictionary entries
  - View user profiles and statistics

- **Authenticated Users**
  - Create new folders, dictionaries, and entries
  - Manage their own content (create, update, delete)
  - Convert their dictionaries to flashcards
  - Generate PDF exports of their content
  - Full access to all public features

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
- `POST /api/account/reset-password-request/`: Request password reset
- `POST /api/account/reset-password/`: Reset password
- `POST /api/account/resend-verification-email/`: Resend verification email
- `POST /api/account/token/refresh/`: Refresh JWT token

### User Profile ###
- `GET /api/account/profile/`: List of all user profiles
- `GET /api/account/profile/{id}/`: Detail page of a user profile
- `PUT/PATCH /api/account/profile/{id}/`: Update user profile
- `DELETE /api/account/profile/{id}/`: Delete user profile

### Folders ###
- `GET /api/folders/`: List of all folders
- `POST /api/folders/`: Create a new folder
- `GET /api/folders/{id}/`: Retrieve a specific folder
- `PUT/PATCH /api/folders/{id}/`: Update a folder
- `DELETE /api/folders/{id}/`: Delete a folder
- `POST /api/folders/{id}/flashcards/`: Turn folder into flashcards
- `GET /api/folders/{id}/pdf/`: Download folder PDF

### Dictionaries ##
- `GET /api/folders/{folder_pk}/dictionaries/`: List all dictionaries inside the folder
- `POST /api/folders/{folder_pk}/dictionaries/`: Create a new dictionary inside the folder
- `GET /api/folders/{folder_pk}/dictionaries/{id}/`: Retrieve a specific dictionary
- `PUT/PATCH /api/folders/{folder_pk}/dictionaries/{id}/`: Update a dictionary
- `DELETE /api/folders/{folder_pk}/dictionaries/{id}/`: Delete a dictionary
- `POST /api/folders/{folder_pk}/dictionaries/{id}/flashcards/`: Turn dictionary into flashcards
- `GET /api/folders/{folder_pk}/dictionaries/{id}/pdf/`: Download dictionary PDF

### Dictionary Entries ###
- `GET /api/folders/{folder_pk}/dictionaries/{dictionary_pk}/entries/`: List all entries inside a dictionary
- `POST /api/folders/{folder_pk}/dictionaries/{dictionary_pk}/entries/`: Create a new word entry inside a dictionary
- `GET /api/folders/{folder_pk}/dictionaries/{dictionary_pk}/entries/{id}/`: Retrieve a specific word
- `PUT/PATCH /api/folders/{folder_pk}/dictionaries/{dictionary_pk}/entries/{id}/`: Update a word
- `DELETE /api/folders/{folder_pk}/dictionaries/{dictionary_pk}/entries/{id}/`: Delete a word
- `POST /api/folders/{folder_pk}/dictionaries/{dictionary_pk}/entries/generate/`: Generate translations and examples

### Search & Leaderboard ###
- `GET /api/search/`: List of all dictionary entries with search functionality
- `GET /api/leaderboard/`: Leaderboard (Overall & Weekly)

  
## Future Improvements ##
This project is part of an ongoing Django, DRF learning journey and has several planned improvements:

### Language Support and Data Sources ###
- Integration with multiple dictionary APIs for more comprehensive word definitions.
- Support for additional languages and writing systems.
- Audio pronunciation support.
- Custom study plans and goals.
- Progress analytics and learning insights.

### User Experience and Interface ###
- Modern, responsive interface with improved navigation and accessibility.
- Interactive study modes and vocabulary learning games.
- Desktop application development.
- Customizable themes and layouts.

**Note**: The current frontend implementation relies on basic HTML, CSS, and JavaScript 
with support from tutorials and AI assistance. Contributions to improve the frontend are welcome and appreciated.


## Acknowledgments ##
- OpenAI for providing the API for translations and example generation.
- Django and Django REST Framework communities for excellent documentation and support.
- TBC and USAID for the course 'Python Advance'.
- I would like to express my sincere gratitude to Tsotne Sharvadze and Giga Samkharadze for their guidance and support.
