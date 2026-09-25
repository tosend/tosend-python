"""ToSend API client."""

import json
from typing import Optional, Dict, Any, List, Union
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from .types import (
    Address,
    SendEmailResponse,
    BatchEmailResponse,
    AccountInfo,
)
from .exceptions import ToSendError

# Sent on every request. Without it urllib identifies as "Python-urllib/x.y",
# which Cloudflare's browser integrity check in front of api.tosend.com
# rejects with "403 error code: 1010" before the request reaches the API.
__version__ = "1.1.1"
USER_AGENT = f"tosend-python/{__version__}"


AddressLike = Union[Address, Dict[str, str]]


class _BaseClient:
    """HTTP plumbing shared by the sending and admin clients."""

    DEFAULT_BASE_URL = "https://api.tosend.com"
    DEFAULT_TIMEOUT = 30

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        if not api_key or not api_key.strip():
            raise ToSendError("API key is required", 401, "unauthorized")

        self.api_key = api_key.strip()
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout or self.DEFAULT_TIMEOUT

    def _to_address_dict(self, address: AddressLike) -> Dict[str, str]:
        """Convert address to dict format."""
        if isinstance(address, Address):
            return address.to_dict()
        return address

    def _build_email(
        self,
        *,
        from_address: AddressLike,
        to: List[AddressLike],
        subject: str,
        html: Optional[str] = None,
        text: Optional[str] = None,
        cc: Optional[List[AddressLike]] = None,
        bcc: Optional[List[AddressLike]] = None,
        reply_to: Optional[AddressLike] = None,
        headers: Optional[Dict[str, str]] = None,
        attachments: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "from": self._to_address_dict(from_address),
            "to": [self._to_address_dict(addr) for addr in to],
            "subject": subject,
        }

        if html:
            data["html"] = html
        if text:
            data["text"] = text
        if cc:
            data["cc"] = [self._to_address_dict(addr) for addr in cc]
        if bcc:
            data["bcc"] = [self._to_address_dict(addr) for addr in bcc]
        if reply_to:
            data["reply_to"] = self._to_address_dict(reply_to)
        if headers:
            data["headers"] = headers
        if attachments:
            data["attachments"] = attachments

        return data

    def _build_batch(self, emails: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not emails:
            raise ToSendError(
                "Emails list is required and cannot be empty",
                422,
                "validation_error",
                {"emails": {"required": "At least one email is required"}},
            )

        processed_emails = []
        for email in emails:
            processed: Dict[str, Any] = {}

            if "from_address" in email:
                processed["from"] = self._to_address_dict(email["from_address"])
            elif "from" in email:
                processed["from"] = self._to_address_dict(email["from"])

            if "to" in email:
                processed["to"] = [self._to_address_dict(addr) for addr in email["to"]]

            for key in ("subject", "html", "text", "headers", "attachments"):
                if key in email:
                    processed[key] = email[key]

            for key in ("cc", "bcc"):
                if key in email and email[key]:
                    processed[key] = [self._to_address_dict(addr) for addr in email[key]]

            if "reply_to" in email and email["reply_to"]:
                processed["reply_to"] = self._to_address_dict(email["reply_to"])

            processed_emails.append(processed)

        return {"emails": processed_emails}

    def _extra_headers(self) -> Dict[str, str]:
        """Headers added to every request. Overridden by the admin client."""
        return {}

    def _request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        query: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an HTTP request to the API."""
        url = f"{self.base_url}{path}"

        if query:
            params = {k: v for k, v in query.items() if v is not None and v != ""}
            if params:
                url += "?" + urlencode(params)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        }
        headers.update(self._extra_headers())

        body = json.dumps(data).encode("utf-8") if data else None

        request = Request(url, data=body, headers=headers, method=method)

        try:
            with urlopen(request, timeout=self.timeout) as response:
                response_body = response.read().decode("utf-8")
                if response_body:
                    return json.loads(response_body)
                return {}
        except HTTPError as e:
            try:
                error_body = e.read().decode("utf-8")
                error_data = json.loads(error_body)
            except (json.JSONDecodeError, UnicodeDecodeError):
                raise ToSendError(str(e), e.code)
            if not isinstance(error_data, dict):
                raise ToSendError(str(e), e.code)
            raise ToSendError.from_response(error_data, e.code)
        except URLError as e:
            raise ToSendError(f"Request failed: {e.reason}")
        except Exception as e:
            raise ToSendError(f"Request failed: {str(e)}")


class ToSend(_BaseClient):
    """ToSend API client."""

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        """
        Initialize ToSend client.

        Args:
            api_key: Your ToSend API key
            base_url: Custom base URL (optional)
            timeout: Request timeout in seconds (optional)
        """
        super().__init__(api_key, base_url, timeout)

    def send(
        self,
        *,
        from_address: AddressLike,
        to: List[AddressLike],
        subject: str,
        html: Optional[str] = None,
        text: Optional[str] = None,
        cc: Optional[List[AddressLike]] = None,
        bcc: Optional[List[AddressLike]] = None,
        reply_to: Optional[AddressLike] = None,
        headers: Optional[Dict[str, str]] = None,
        attachments: Optional[List[Dict[str, str]]] = None,
    ) -> SendEmailResponse:
        """
        Send a single email.

        Args:
            from_address: Sender address
            to: List of recipient addresses
            subject: Email subject
            html: HTML content
            text: Plain text content
            cc: CC recipients
            bcc: BCC recipients
            reply_to: Reply-to address
            headers: Custom headers
            attachments: File attachments

        Returns:
            SendEmailResponse with message_id
        """
        data = self._build_email(
            from_address=from_address, to=to, subject=subject, html=html, text=text,
            cc=cc, bcc=bcc, reply_to=reply_to, headers=headers, attachments=attachments,
        )
        response = self._request("POST", "/v2/emails", data)
        return SendEmailResponse.from_dict(response)

    def batch(
        self,
        emails: List[Dict[str, Any]],
    ) -> BatchEmailResponse:
        """
        Send multiple emails in a single request.

        Args:
            emails: List of email objects (same format as send())

        Returns:
            BatchEmailResponse with results for each email
        """
        response = self._request("POST", "/v2/emails/batch", self._build_batch(emails))
        return BatchEmailResponse.from_dict(response)

    def get_account_info(self) -> AccountInfo:
        """
        Get account information and domains.

        Returns:
            AccountInfo with account details and domains
        """
        response = self._request("GET", "/v2/info")
        return AccountInfo.from_dict(response)
