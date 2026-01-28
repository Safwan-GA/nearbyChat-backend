import firebase_admin
from firebase_admin import credentials, firestore, messaging, auth
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
cred_path = BASE_DIR / "firebase" / "serviceAccountKey.json"

cred = credentials.Certificate(cred_path)

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()
fcm = messaging
firebase_auth = auth
