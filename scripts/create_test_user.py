#!/usr/bin/env python3
"""Create a test user in Firebase Auth."""

import firebase_admin
from firebase_admin import credentials, auth
import os

# Initialize Firebase Admin with service account
service_account_path = os.path.join(os.path.dirname(__file__), '..', 'service-account.json')
cred = credentials.Certificate(service_account_path)

try:
    firebase_admin.initialize_app(cred)
except ValueError:
    # Already initialized
    pass

# Create test user
email = "tosh.test@example.com"
password = "TestPassword123!"

try:
    # Try to get existing user
    user = auth.get_user_by_email(email)
    print(f"User already exists: {user.uid}")
except auth.UserNotFoundError:
    # Create new user
    user = auth.create_user(
        email=email,
        password=password,
        email_verified=True,
        display_name="Tosh Test User"
    )
    print(f"Created user: {user.uid}")
    print(f"Email: {email}")
    print(f"Password: {password}")
