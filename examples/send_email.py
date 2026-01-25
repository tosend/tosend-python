"""Example: Send a single email."""

import os
from tosend import ToSend, ToSendError

api_key = os.environ.get("TOSEND_API_KEY")
if not api_key:
    print("Error: TOSEND_API_KEY environment variable is required")
    exit(1)

client = ToSend(api_key)

try:
    response = client.send(
        from_address={"email": "hello@yourdomain.com", "name": "Your App"},
        to=[{"email": "user@example.com", "name": "John Doe"}],
        subject="Welcome to ToSend!",
        html="<h1>Hello!</h1><p>Thanks for signing up.</p>",
        text="Hello! Thanks for signing up.",
    )

    print("Email sent successfully!")
    print(f"Message ID: {response.message_id}")

except ToSendError as e:
    print(f"API Error: {e.message} (status: {e.status_code})")
    if e.errors:
        print(f"Details: {e.errors}")
