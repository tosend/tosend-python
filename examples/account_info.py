"""Example: Get account information."""

import os
from tosend import ToSend, ToSendError

api_key = os.environ.get("TOSEND_API_KEY")
if not api_key:
    print("Error: TOSEND_API_KEY environment variable is required")
    exit(1)

client = ToSend(api_key)

try:
    info = client.get_account_info()

    print("=== Account Information ===\n")
    print(f"Account:      {info.account.id}")
    print(f"Plan:         {info.account.plan_type}")
    print(f"Status:       {info.account.status}")
    print(f"Credits:      {info.account.credit_balance}")
    print(f"Rate limit:   {info.account.limit_per_second}/s")
    print()

    print("=== Domains ===\n")
    if not info.domains:
        print("No domains configured")
    else:
        for domain in info.domains:
            print(f"- {domain.domain_name} ({domain.verification_status})")

except ToSendError as e:
    print(f"API Error: {e.message} (status: {e.status_code})")
