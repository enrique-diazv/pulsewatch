import os

os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_PASSWORD"] = "test-password"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-with-at-least-32-characters"
