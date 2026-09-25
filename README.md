# ToSend Python SDK

Official Python SDK for the [ToSend](https://tosend.com) email API.

[![PyPI version](https://badge.fury.io/py/tosend.svg)](https://badge.fury.io/py/tosend)
[![Python Versions](https://img.shields.io/pypi/pyversions/tosend.svg)](https://pypi.org/project/tosend/)

## Installation

```bash
pip install tosend
```

## Examples

See the [examples](examples) folder for complete working examples:

- [Send Email](examples/send_email.py) - Send a single email
- [Batch Send](examples/batch_send.py) - Send multiple emails in one request
- [Account Info](examples/account_info.py) - Get account information and domains

```bash
export TOSEND_API_KEY=tsend_your_api_key
python examples/send_email.py
```

## Quick Start

```python
from tosend import ToSend

client = ToSend("tsend_your_api_key")

response = client.send(
    from_address={"email": "hello@yourdomain.com", "name": "Your App"},
    to=[{"email": "user@example.com"}],
    subject="Welcome!",
    html="<h1>Hello!</h1><p>Thanks for signing up.</p>",
)

print(response.message_id)
```

## Usage

### Send an Email

```python
response = client.send(
    from_address={"email": "hello@yourdomain.com", "name": "Your App"},
    to=[
        {"email": "user@example.com"},
        {"email": "another@example.com", "name": "John Doe"},
    ],
    subject="Hello!",
    html="<h1>Welcome</h1>",
    text="Welcome",  # optional
)
```

### With CC, BCC, and Reply-To

```python
response = client.send(
    from_address={"email": "hello@yourdomain.com"},
    to=[{"email": "user@example.com"}],
    cc=[{"email": "cc@example.com"}],
    bcc=[{"email": "bcc@example.com"}],
    reply_to={"email": "support@yourdomain.com", "name": "Support"},
    subject="Hello",
    html="<p>Hello World</p>",
)
```

### With Attachments

```python
import base64

with open("invoice.pdf", "rb") as f:
    content = base64.b64encode(f.read()).decode()

response = client.send(
    from_address={"email": "hello@yourdomain.com"},
    to=[{"email": "user@example.com"}],
    subject="Your Invoice",
    html="<p>Please find your invoice attached.</p>",
    attachments=[
        {
            "type": "application/pdf",
            "name": "invoice.pdf",
            "content": content,
        }
    ],
)
```

### Batch Sending

Send multiple emails in a single request:

```python
response = client.batch([
    {
        "from": {"email": "hello@yourdomain.com"},
        "to": [{"email": "user1@example.com"}],
        "subject": "Hello User 1",
        "html": "<p>Welcome!</p>",
    },
    {
        "from": {"email": "hello@yourdomain.com"},
        "to": [{"email": "user2@example.com"}],
        "subject": "Hello User 2",
        "html": "<p>Welcome!</p>",
    },
])

for result in response.results:
    if result.status == "success":
        print(f"Sent: {result.message_id}")
    else:
        print(f"Failed: {result.message}")
```

### Get Account Info

```python
info = client.get_account_info()

print(info.account.status)            # "active"
print(info.account.credit_balance)    # None means the account does not consume credits
print(info.account.limit_per_second)
print(info.account.bounce_rate)       # a fraction between 0 and 1

for domain in info.domains:
    print(f"{domain.domain_name}: {domain.verification_status}")
```

## Admin API

`ToSendAdmin` is a separate client for the [Admin API](https://tosend.com/docs/api/admin-api). It takes an admin key (`tsend_admin_...`) and refuses a sending key at construction. Each call needs the matching [scope](https://tosend.com/docs/api/admin-api#scopes) on the key; a missing one raises `ToSendError` with status 403 and `error.code == "insufficient_scope"`.

```python
import os
from tosend import ToSendAdmin

admin = ToSendAdmin(os.environ["TOSEND_ADMIN_KEY"])

# Act on one of your client teams (sends X-Account-Id)
client = admin.for_account(4203)

domain = client.create_domain("client.example.com")
detail = client.get_domain(domain["id"])
print(detail["dns_records"]["dkim"])  # show these records to your client

# Needs api_keys:write and emails:send
key = client.create_sending_key("Client: Acme Corp")
print(key["api_key"])  # returned once, store it now

# Needs emails:send
client.send(
    from_address={"email": "hello@client.example.com"},
    to=[{"email": "user@example.com"}],
    subject="Hi",
    html="<p>Hello</p>",
)
```

Also available: `get_info`, `list_domains`, `delete_domain`, `list_emails`, `get_email`, `list_suppressions`, `delete_suppression`, `list_webhooks`, `create_webhook`, `update_webhook`, `delete_webhook`, `list_sending_keys`, `delete_sending_key`, `list_teams`, `create_team`, `update_team` and `batch`. List methods take `page` and `per_page` and return a dict with `data`, `total`, `page` and `per_page`; single-resource methods return the resource as a dict.

## Configuration

### With Options

```python
client = ToSend(
    api_key="tsend_your_api_key",
    base_url="https://api.tosend.com",  # optional
    timeout=60,  # optional, in seconds
)
```

## Error Handling

```python
from tosend import ToSend, ToSendError

client = ToSend("tsend_your_api_key")

try:
    response = client.send(
        from_address={"email": "hello@yourdomain.com"},
        to=[{"email": "user@example.com"}],
        subject="Hello",
        html="<p>Hello</p>",
    )
except ToSendError as e:
    print(f"Error: {e.message}")
    print(f"Status: {e.status_code}")
    print(f"Type: {e.error_type}")
    print(f"Details: {e.errors}")

    if e.is_validation_error:
        # Handle validation error (422)
        pass

    if e.is_authentication_error:
        # Handle auth error (401/403)
        pass

    if e.is_rate_limit_error:
        # Handle rate limit (429)
        pass
```

## Type Hints

The SDK includes full type hints. You can also use the provided dataclasses:

```python
from tosend import ToSend, Address, SendEmailRequest

client = ToSend("tsend_your_api_key")

# Using Address dataclass
from_addr = Address(email="hello@yourdomain.com", name="Your App")
to_addr = Address(email="user@example.com")

response = client.send(
    from_address=from_addr,
    to=[to_addr],
    subject="Hello!",
    html="<h1>Welcome!</h1>",
)
```

## Requirements

- Python 3.8 or higher
- No external dependencies (uses only standard library)

## License

MIT
