"""
XBlock settings
"""

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        # 'NAME': 'intentionally-omitted',
    },
}
INSTALLED_APPS = (
    # 'sql_grader',
)
LOCALE_PATHS = [
    'sql_grader/translations',
]
SECRET_KEY = 'SECRET_KEY'
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'
