# Tordi

A WhatsApp-style chat app built with Django and phone-number + OTP
authentication. Messaging is HTTP-polling based (not WebSockets), so it
runs on ordinary WSGI hosting — including free tiers like PythonAnywhere
— with no extra infrastructure (no Redis, no ASGI server needed).

## What's included

- **Phone number registration/login** — no usernames or emails. A 6-digit
  code is texted to the person's real phone via Twilio (SMS or WhatsApp),
  or printed to the console if Twilio isn't configured — see "OTP delivery"
  below.
- **Custom `User` model** (`accounts.User`) keyed on `phone_number`, with
  name, about text, avatar, and last-seen based online status.
- **One-to-one chat that updates every ~2.5 seconds** via polling
  (`chat/views.py: poll_messages`) — no WebSockets, no Channels/Daphne.
- **Photos and videos** in messages, an emoji picker, contact search,
  a typing indicator, and read receipts.
- A colorful, responsive UI (single Django template stack + vanilla JS,
  no frontend framework) that adapts between mobile and desktop layouts.

## Project layout

```
tordi/
  tordi/         # settings, URLs, WSGI entrypoint
  accounts/      # custom User model, OTP model, registration/login/settings views
  chat/          # Conversation/Message models, views (incl. polling endpoints)
  templates/     # HTML templates (accounts/, chat/)
  static/        # CSS + JS (style.css, app.js, chat.js)
```

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser   # optional, for /admin/
python manage.py runserver
```

Then visit `http://127.0.0.1:8000/accounts/register/`.

## OTP delivery: real SMS or WhatsApp via Twilio

Tordi sends the OTP for real if Twilio credentials are present as
environment variables; otherwise it prints the code to your terminal so
local development never gets you locked out.

Set these (or copy `.env.example` to `.env` and fill it in — it's loaded
automatically and gitignored so secrets never get committed):

```bash
export TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
export TWILIO_AUTH_TOKEN=your_auth_token
export TWILIO_FROM_NUMBER=+15551234567     # your Twilio number, for SMS
```

For WhatsApp instead of SMS:
```bash
export TWILIO_USE_WHATSAPP=true
export TWILIO_WHATSAPP_FROM=+14155238886   # Twilio's shared sandbox number while testing
```
With the sandbox, each recipient must first send "join &lt;code&gt;" to that
number from their own WhatsApp before they can receive messages — that's
a Twilio/Meta requirement, not something the code can skip. Moving to a
real WhatsApp sender number requires Meta business verification.

**Trial Twilio accounts** can only message numbers you've explicitly
verified in the Twilio console (Console → Phone Numbers → Verified Caller
IDs) — up to 5 of them. To message arbitrary new users, you'll need to
upgrade the Twilio account (billing) and complete number registration
(A2P 10DLC for a standard US number, or toll-free verification).

No code changes are needed for any of this — `accounts/views.py:send_otp_sms()`
already handles it, controlled entirely by environment variables.

## Deploying to PythonAnywhere

1. Upload the project (zip upload, or `git clone` in a Bash console if
   you push this to a repo) into your PythonAnywhere home directory.
2. In a PythonAnywhere Bash console:
   ```bash
   cd tordi
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py createsuperuser
   ```
3. On the **Web** tab, create a new web app → choose **Manual configuration**
   → your Python version → point it at this project.
4. Edit the generated WSGI file (linked from the Web tab) so it loads
   Tordi's settings, e.g.:
   ```python
   import sys
   path = '/home/yourusername/tordi'
   if path not in sys.path:
       sys.path.insert(0, path)
   import os
   os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tordi.settings')
   from django.core.wsgi import get_wsgi_application
   application = get_wsgi_application()
   ```
5. On the **Virtualenv** section of the Web tab, point it at the venv you
   created in step 2.
6. Set **Static files** mappings: URL `/static/` → your `static/` folder
   (after running `python manage.py collectstatic`), and `/media/` → your
   `media/` folder.
7. Either upload a `.env` file with your Twilio credentials into the
   project root (it's picked up automatically), or set them as actual
   environment variables — PythonAnywhere's paid plans expose an
   "Environment variables" section on the Web tab for this.
8. Reload the web app from the Web tab. Registration, login, and chat
   (via polling) will all work on standard WSGI hosting — no ASGI/
   WebSocket support needed, which PythonAnywhere doesn't offer on
   normal web app hosting anyway.

Before letting real people use it, also do the items in "Security notes"
below — `DEBUG = True` and a placeholder `SECRET_KEY` are fine for your
own testing, not for other people's phone numbers and messages.

## How the polling works (if you're curious or want to tune it)

- The room page remembers the id of the newest message it has.
- Every 2.5 seconds (`static/js/chat.js`), it calls
  `GET /room/<id>/poll/?after=<last_id>`, which returns any newer
  messages plus whether the other person is typing/online.
- Sending a message or attachment is a normal `POST` (`send_message` /
  `upload_attachment` in `chat/views.py`); the response includes the new
  message so it appears instantly for the sender without waiting for the
  next poll. The other person picks it up on their next poll cycle.
- "Online" is computed from `User.last_seen` — any request from a device
  refreshes it, and someone is considered online if that timestamp is
  under 20 seconds old (`User.ONLINE_THRESHOLD_SECONDS` in `accounts/models.py`).
- The typing indicator uses Django's cache framework (in-memory by
  default) with a 3-second expiry — no database writes needed for it.

If you want closer-to-instant delivery, lower the 2500ms interval in
`chat.js`, keeping in mind more frequent polling means more requests per
open chat window.

## Natural next features to add

- Group chats (the `Conversation.is_group` field and UI hook are already there)
- Push notifications for messages received while offline
- Message delete/edit, blocking, and rate limiting on OTP requests
- Proper phone number validation/formatting (e.g. via the `phonenumbers` package)
- A database-backed cache (instead of the default in-memory one) if you
  deploy behind multiple worker processes, so the typing indicator stays
  reliable across all of them

## Security notes before deploying for real

- Change `SECRET_KEY` in `settings.py` and load it from an environment
  variable rather than leaving the placeholder in the file.
- Set `DEBUG = False` and a real `ALLOWED_HOSTS` list.
- Add rate limiting to OTP requests (currently unlimited) to prevent abuse
  and unexpected Twilio charges.
- Serve static/media files via a proper storage backend (S3, etc.) for
  anything beyond light personal testing.
- Rotate any Twilio credentials that were ever typed into a chat, commit,
  or shared file — treat them as compromised the moment they leave the
  Twilio console.
