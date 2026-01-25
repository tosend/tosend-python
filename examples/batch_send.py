"""Example: Send multiple emails in a batch."""

import os
from tosend import ToSend, ToSendError

api_key = os.environ.get("TOSEND_API_KEY")
if not api_key:
    print("Error: TOSEND_API_KEY environment variable is required")
    exit(1)

client = ToSend(api_key)

emails = [
    {
        "from": {"email": "hello@yourdomain.com", "name": "Your App"},
        "to": [{"email": "user1@example.com"}],
        "subject": "Hello User 1",
        "html": "<p>Welcome to our platform!</p>",
    },
    {
        "from": {"email": "hello@yourdomain.com", "name": "Your App"},
        "to": [{"email": "user2@example.com"}],
        "subject": "Hello User 2",
        "html": "<p>Welcome to our platform!</p>",
    },
    {
        "from": {"email": "hello@yourdomain.com", "name": "Your App"},
        "to": [{"email": "user3@example.com"}],
        "subject": "Hello User 3",
        "html": "<p>Welcome to our platform!</p>",
    },
]

try:
    response = client.batch(emails)

    print(f"Batch sent! Processing {len(response.results)} emails:\n")

    for i, result in enumerate(response.results, 1):
        if result.status == "success":
            print(f"[{i}] Success - Message ID: {result.message_id}")
        else:
            print(f"[{i}] Failed - {result.message}")

except ToSendError as e:
    print(f"API Error: {e.message} (status: {e.status_code})")
