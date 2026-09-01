# Tordi

A WhatsApp-style chat app built with Django, Django Channels (WebSockets), and
phone-number + OTP authentication.

## What's included

- **Phone number registration/login** — no usernames or emails. A 6-digit
  code is generated and, in dev mode, printed to the console instead of
  being sent by SMS (see "Going live" below).
- **Custom `User` model** (`accounts.User`) keyed on `phone_number`, with
  name, about text, avatar, online status, and last-seen.
- **One-to-one real-time chat** over WebSockets (`chat.consumers.ChatConsumer`)
  — messages appear instantly for both people without a page refresh.
- **Contact search** — find anyone by phone number or name and start a chat.
- **Typing indicator** and **online/last-seen status**.
- **Read receipts** at the model level (`Message.is_read`) — messages are
  marked read when the recipient opens the conversation.
- A WhatsApp-inspired UI (green/teal theme, message bubbles) with no
  front-end framework — just Django templates + vanilla JS.

## Project layout

```
tordi/
  tordi/         # settings, URLs, ASGI/WSGI entrypoints
  accounts/      # custom User model, OTP model, registration/login views
  chat/          # Conversation/Message models, views, WebSocket consumer
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
```

## Running it

Because this uses WebSockets, run it with Daphne (an ASGI server) rather
than `runserver` in production. For local development, `runserver` will
also work since Django auto-detects the ASGI app:

```bash
python manage.py runserver
```

or explicitly with Daphne:

```bash
daphne -b 0.0.0.0 -p 8000 tordi.asgi:application
```

Then visit `http://127.0.0.1:8000/accounts/register/`.

Since there's no real SMS provider wired up yet, the OTP code is printed to
your terminal — copy it into the verification screen.

## Going live: connecting a real SMS provider

Open `accounts/views.py` and look at `send_otp_sms()`. Swap the `print()`
line for a real provider call, e.g. Twilio:

```python
from twilio.rest import Client
from django.conf import settings

def send_otp_sms(phone_number, code):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    client.messages.create(
        body=f"Your Tordi verification code is {code}",
        from_=settings.TWILIO_FROM_NUMBER,
        to=phone_number,
    )
```

Set `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, and `TWILIO_FROM_NUMBER` as
environment variables (already read in `settings.py`).

## Scaling past a single dev server

The default channel layer (`InMemoryChannelLayer`) only works within a
single process — fine for development, but it won't relay messages between
multiple Daphne workers or servers. For production, install Redis and
switch `CHANNEL_LAYERS` in `settings.py` to `channels_redis.core.RedisChannelLayer`
(the config block is already there, commented out).

## Natural next features to add

- Group chats (the `Conversation.is_group` field and UI hook are already there)
- Media/file attachments in messages (`Message.attachment` field exists;
  wire up file input + display in `chat.js`/`room.html`)
- Push notifications for messages received while offline
- Message delete/edit, blocking, and rate limiting on OTP requests
- Proper phone number validation/formatting (e.g. via the `phonenumbers` package)

## Security notes before deploying

- Change `SECRET_KEY` in `settings.py` and load it from an environment variable.
- Set `DEBUG = False` and a real `ALLOWED_HOSTS` list.
- Add rate limiting to OTP requests (currently unlimited) to prevent abuse.
- Serve static/media files via a proper storage backend (S3, etc.) rather
  than Django's dev file serving.
