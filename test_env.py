#!/usr/bin/env python3
"""Test environment variables and login."""

import os
import sys

print("=== Environment Variables ===")
print(f"AUTH_USERNAME from env: '{os.environ.get('AUTH_USERNAME', 'NOT SET')}'")
print(f"AUTH_PASSWORD from env: '{os.environ.get('AUTH_PASSWORD', 'NOT SET')}'")
print(f"SECRET_KEY from env: '{os.environ.get('SECRET_KEY', 'NOT SET')}'")
print(f"DEBUG from env: '{os.environ.get('DEBUG', 'NOT SET')}'")
print()

# Test what the app would see
from app.server import create_app

app = create_app()

print("=== App Configuration ===")
print(f"AUTH_USERNAME in config: '{app.config.get('AUTH_USERNAME')}'")
print(f"AUTH_PASSWORD in config: '{app.config.get('AUTH_PASSWORD')}'")
print(f"SECRET_KEY length: {len(app.config.get('SECRET_KEY', ''))}")
print(f"Debug mode: {app.debug}")
print()

# Test constant-time comparison
import secrets

test_username = input("Enter test username: ")
test_password = input("Enter test password: ")

username_valid = secrets.compare_digest(test_username, app.config.get('AUTH_USERNAME'))
password_valid = secrets.compare_digest(test_password, app.config.get('AUTH_PASSWORD'))

print()
print("=== Login Test ===")
print(f"Username match: {username_valid}")
print(f"Password match: {password_valid}")
print(f"Login would succeed: {username_valid and password_valid}")
