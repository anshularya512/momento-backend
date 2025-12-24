import os
import json
import firebase_admin
from firebase_admin import credentials, messaging

# Prevent double initialization
if not firebase_admin._apps:
    cred = credentials.Certificate(
        json.loads(os.getenv("FIREBASE_CREDENTIALS"))
    )
    firebase_admin.initialize_app(cred)


def send_push(token: str, title: str, body: str):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        token=token
    )
    messaging.send(message)
