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

## Going live: sending the OTP to a real phone (SMS or WhatsApp)

By default Tordi prints the OTP code to your terminal — good for local
testing, useless for real users. To send it to their actual phone, wire up
Twilio (a few minutes, free trial available):

1. Create a free account at https://www.twilio.com/try-twilio and verify
   your own phone number (trial accounts can only message verified numbers
   until you upgrade).
2. From the Twilio Console dashboard, copy your **Account SID** and
   **Auth Token**.
3. Install the SDK: `pip install twilio` (already in `requirements.txt`).
4. Choose SMS or WhatsApp:

   **SMS** — Twilio gives trial accounts a free phone number under
   *Phone Numbers → Manage → Active Numbers*. Set:
   ```bash
   export TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   export TWILIO_AUTH_TOKEN=your_auth_token
   export TWILIO_FROM_NUMBER=+15551234567
   ```

   **WhatsApp** — Twilio's sandbox lets you test WhatsApp delivery for free.
   Under *Messaging → Try it out → Send a WhatsApp message*, follow the
   instructions to join the sandbox from your own WhatsApp (send the given
   code to their sandbox number). Then set:
   ```bash
   export TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   export TWILIO_AUTH_TOKEN=your_auth_token
   export TWILIO_USE_WHATSAPP=true
   export TWILIO_WHATSAPP_FROM=+14155238886
   ```
   (`+14155238886` is Twilio's shared sandbox number — yours may differ,
   check the console.) Note: with the sandbox, only numbers that joined it
   can receive messages. Moving to a production WhatsApp sender requires
   Meta business verification through Twilio.

5. Restart the server. Registration/login will now message the real
   number; if Twilio isn't configured or a send fails, Tordi automatically
   falls back to printing the code to the console so you're never locked
   out during development.

No code changes are needed for either path — `accounts/views.py:send_otp_sms()`
already handles both, controlled entirely by the environment variables above.

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
