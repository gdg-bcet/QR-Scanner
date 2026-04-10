import os
import base64
import time
from email.message import EmailMessage
import mimetypes

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# We will reuse your existing SheetsDB to get the list of people
from sheets_db import SheetsDB

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

QR_DIR = os.path.join(os.path.dirname(__file__), "qrcodes")

def get_gmail_service():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    token_path = os.path.join(os.path.dirname(__file__), 'token.json')
    client_secret_path = os.path.join(os.path.dirname(__file__), 'gmail_credentials.json')

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(client_secret_path):
                print(f"❌ Error: {client_secret_path} not found.")
                print("⚠️ You cannot use your Service Account for sending emails from your personal account.")
                print("1. Go to Google Cloud Console")
                print("2. Create an 'OAuth client ID' (Desktop App)")
                print("3. Download JSON and save it as 'gmail_credentials.json'")
                exit(1)

            flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    try:
        service = build("gmail", "v1", credentials=creds)
        return service
    except Exception as error:
        print(f"An error occurred: {error}")
        return None

def send_email_with_attachment(service, to_email: str, name: str, size: str, filepath: str):
    """Create and send an email message with the QR code."""
    try:
        message = EmailMessage()

        # HTML Content
        content = f"""
        <html>
          <body>
            <h2>Hi {name},</h2>
            <p>Your Google Cloud Study Jams 2025 T-Shirt (Size: <strong>{size}</strong>) is ready!</p>
            <p>Please find your unique QR code attached to this email. You can present this QR code safely from your phone to collect your T-shirt.</p>
            <p>If you are unavailable, you may forward this email/QR code to a friend who can collect it on your behalf.</p>
            <br>
            <p>Best regards,<br>The organizing team.</p>
          </body>
        </html>
        """

        message.set_content("Please enable HTML to view this email.")
        message.add_alternative(content, subtype='html')

        message['To'] = to_email
        message['From'] = "me" # "me" refers to the authenticated user
        message['Subject'] = "🎫 Your Cloud Study Jams T-Shirt QR Code"

        # Attach the QR code
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        # Guess MIME type
        mime_type, _ = mimetypes.guess_type(filepath)
        mime_type, mime_subtype = mime_type.split('/', 1)

        with open(filepath, 'rb') as fp:
            attachment_data = fp.read()
        
        message.add_attachment(
            attachment_data,
            maintype=mime_type,
            subtype=mime_subtype,
            filename="TShirt_QRCode.png"
        )

        # Base64 encode the message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': encoded_message}

        # Send
        send_message = service.users().messages().send(userId="me", body=create_message).execute()
        return True, send_message['id']

    except Exception as error:
        return False, str(error)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Send QR Code Emails")
    parser.add_argument("--test-email", type=str, help="Run a trial sending the first QR code to this specific email.")
    parser.add_argument("--confirm", action="store_true", help="Confirm you want to mass mail everyone.")
    args = parser.parse_args()

    if not args.test_email and not args.confirm:
        print("⚠️  SAFETY LOCK: By default, this script will NOT mass mail.")
        print("    To mass email ALL participants, you must run:")
        print("    python send_emails.py --confirm\n")
        print("    To run a trial to see what the email looks like, run:")
        print("    python send_emails.py --test-email YOUR_OWN_EMAIL@gmail.com")
        return

    print("📧 Initializing Gmail API...")
    gmail_service = get_gmail_service()
    if not gmail_service:
        return

    print("🔗 Connecting to Google Sheets to read users...")
    db = SheetsDB()
    records = db.get_all_records()

    if args.test_email:
        print(f"🛠️  TRIAL MODE: Will only send the FIRST participant's email to '{args.test_email}'")
        # We only take the first record to generate a test email, but we send it to args.test_email
        records = records[:1]

    print(f"📋 Generating emails...\n")

    sent = 0
    failed = 0

    for record in records:
        token = record["token_id"]
        name = record["name"]
        size = record["tshirt_size"]
        
        # If testing, override the recipient to the test email
        email = args.test_email if args.test_email else record["email"]

        if not email:
            print(f"  ⚠️  Skipping {name} (token: {token}) - No email address")
            failed += 1
            continue

        # Construct file name string (same rule as generate_qrcodes.py)
        safe_name = "".join(c if c.isalnum() or c in (" ", "-", "_") else "" for c in name).strip()
        filename = f"{token}_{safe_name}.png"
        filepath = os.path.join(QR_DIR, filename)

        if not os.path.exists(filepath):
            print(f"  ❌ Failed for {name}: QR Code image not found at {filepath}")
            failed += 1
            continue

        print(f"  ⏳ Sending email to {email} (For person: {name})... ", end="", flush=True)
        
        success, msg_id = send_email_with_attachment(gmail_service, email, name, size, filepath)
        
        if success:
            print(f"✅ Sent!")
            sent += 1
        else:
            print(f"❌ Error: {msg_id}")
            failed += 1
        
        # small delay to prevent hitting gmail limits too fast
        time.sleep(0.5)

    print(f"\n{'='*60}")
    print(f"✅ Emails Sent:   {sent}")
    print(f"⚠️  Failed/Skipped: {failed}")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
