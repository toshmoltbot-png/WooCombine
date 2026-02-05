#!/usr/bin/env python3
"""Reset test user password in Firebase Auth."""

import firebase_admin
from firebase_admin import credentials, auth
import os

# Initialize Firebase Admin with service account
service_account_path = os.path.join(os.path.dirname(__file__), '..', 'service-account.json')
cred = credentials.Certificate(service_account_path)

try:
    firebase_admin.initialize_app(cred)
except ValueError:
    pass

email = "tosh.test@example.com"
new_password = "TestPassword123!"

try:
    user = auth.get_user_by_email(email)
    auth.update_user(user.uid, password=new_password)
    print(f"Password reset for: {email}")
    print(f"New password: {new_password}")
except Exception as e:
    print(f"Error: {e}")
