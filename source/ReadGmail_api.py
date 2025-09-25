import os
import pickle
# Gmail API utils
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
# for encoding/decoding messages in base64
from base64 import urlsafe_b64decode, urlsafe_b64encode
# for dealing with attachement MIME types
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from mimetypes import guess_type as guess_mime_type

# Request all access (permission to read/send/receive emails, manage the inbox, and more)
SCOPES = ['https://mail.google.com/']
our_email = 'brianzaticinonet@gmail.com'

def gmail_authenticate():
    creds = None
    # the file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # if there are no (valid) credentials availablle, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

# get the Gmail API service
service = gmail_authenticate()

def search_messages_with_subject_prefix(service, user_id='me', subject_prefix='/^'):
    query = f'subject:"{subject_prefix}"'  # cerca le email con '/^' nell'oggetto
    messages = []
    result = service.users().messages().list(userId=user_id, q=query, maxResults=10).execute()
    
    if 'messages' in result:
        messages.extend(result['messages'])

    next_page_token = result.get('nextPageToken')
    # continua a cercare se ci sono altre pagine di risultati
    while next_page_token in result:
        result = service.users().messages().list(
            userId=user_id, q=query, pageToken=next_page_token
        ).execute()
        
        if 'messages' in result:
            messages.extend(result['messages'])
        next_page_token = result.get('nextPageToken')

    print(f"Totale messaggi trovati: {len(messages)}")

    for msg in messages:
        msg_data = service.users().messages().get(userId=user_id, id=msg['id'], format='full').execute()
        headers = msg_data['payload']['headers']

        subject = sender = date = ''

        for header in headers:
            name = header['name'].lower()
            if name == 'subject':
                subject = header['value']
            elif name == 'from':
                sender = header['value']
            elif name == 'date':
                date = header['value']

        if subject.startswith(subject_prefix):
            print(f"\n📬 Oggetto: {subject}")
            print(f"👤 Mittente: {sender}")
            print(f"📅 Data: {date}")
            # Estrai corpo del messaggio
            message_body = get_message_body(msg_data['payload'])
            print(f"Contenuto:\n{message_body}")

            # ✅ Elimina il messaggio
            service.users().messages().delete(userId=user_id, id=msg['id']).execute()
            print("🗑️ Messaggio eliminato.")
            return message_body

def get_message_body(payload):
    parts = payload.get('parts')
    if parts:
        for part in parts:
            mime_type = part.get('mimeType')
            body = part.get('body', {})
            data = body.get('data')
            if data:
                decoded_data = urlsafe_b64decode(data).decode('utf-8')
                return decoded_data
    else:
        body = payload.get('body', {})
        data = body.get('data')
        if data:
            decoded_data = urlsafe_b64decode(data).decode('utf-8')
            return decoded_data
    return "(nessun contenuto leggibile)"

def Leggi():
    testo = search_messages_with_subject_prefix(service)
    return testo
