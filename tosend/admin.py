"""ToSend Admin API client."""

import copy
from typing import Optional, Dict, Any, List
from urllib.parse import quote

from .client import _BaseClient, AddressLike
from .exceptions import ToSendError
from .types import SendEmailResponse, BatchEmailResponse


ADMIN_KEY_PREFIX = "tsend_admin_"


def _segment(value: Any) -> str:
    """Encode one path segment, so an id can never change the path."""
    return quote(str(value), safe="")


class ToSendAdmin(_BaseClient):
    """
    Account-level API client.

    Deliberately a separate class from ``ToSend``: admin keys and sending keys
    are different credentials and are not interchangeable. A sending key
    cannot manage the account, and an admin key can only send when it holds
    the ``emails:send`` scope. Each call needs the matching scope on the key;
    a missing one raises ``ToSendError`` with status 403 and
    ``error.code == "insufficient_scope"``.

    Example::

        admin = ToSendAdmin(os.environ["TOSEND_ADMIN_KEY"])

        domain = admin.create_domain("client.example.com")
        detail = admin.get_domain(domain["id"])
        print(detail["dns_records"]["dkim"])
        # No verify call needed: toSend checks DNS every 10 minutes.

    Single-resource calls return the ``data`` object as a dict. List calls
    return the whole page: ``{"data": [...], "total", "page", "per_page"}``.
    """

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        account_id: Optional[int] = None,
    ):
        """
        Args:
            api_key: Your admin API key (tsend_admin_...)
            base_url: Custom base URL (optional)
            timeout: Request timeout in seconds (optional)
            account_id: Act on this child team by default (optional)
        """
        if not api_key or not api_key.strip():
            raise ToSendError("Admin API key is required", 401, "unauthorized")

        # Caught here rather than as a 401 from the server, because pasting a
        # sending key is the likeliest mistake and the message should say so.
        if not api_key.strip().startswith(ADMIN_KEY_PREFIX):
            raise ToSendError(
                'This is not an admin API key. Admin keys start with "tsend_admin_" '
                "and are created in the dashboard under API Keys.",
                401,
                "unauthorized",
            )

        super().__init__(api_key, base_url, timeout)
        self.account_id = account_id

    def for_account(self, account_id: int) -> "ToSendAdmin":
        """Return a client scoped to one of your child teams (sends X-Account-Id)."""
        clone = copy.copy(self)
        clone.account_id = account_id
        return clone

    def _extra_headers(self) -> Dict[str, str]:
        if self.account_id is None:
            return {}
        return {"X-Account-Id": str(self.account_id)}

    def _data(self, response: Dict[str, Any]) -> Dict[str, Any]:
        return response.get("data") or {}

    # ── Account ──

    def get_info(self) -> Dict[str, Any]:
        """
        The team this key acts on, the key itself and its scopes. Needs no
        scope, so it is the way to check a key works. ``domains`` is present
        only when the key has ``domains:read``.
        """
        return self._request("GET", "/v2/info")

    # ── Sending (requires the emails:send scope) ──

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
        Send an email as the targeted team (the key's own, or one set with
        for_account()). The key must hold the ``emails:send`` scope.
        """
        data = self._build_email(
            from_address=from_address, to=to, subject=subject, html=html, text=text,
            cc=cc, bcc=bcc, reply_to=reply_to, headers=headers, attachments=attachments,
        )
        return SendEmailResponse.from_dict(self._request("POST", "/v2/emails", data))

    def batch(self, emails: List[Dict[str, Any]]) -> BatchEmailResponse:
        """Send up to 100 emails in one request; same scope and targeting as send()."""
        response = self._request("POST", "/v2/emails/batch", self._build_batch(emails))
        return BatchEmailResponse.from_dict(response)

    # ── Domains ──

    def list_domains(self, page: Optional[int] = None, per_page: Optional[int] = None) -> Dict[str, Any]:
        return self._request("GET", "/v2/domains", query={"page": page, "per_page": per_page})

    def create_domain(self, name: str) -> Dict[str, Any]:
        """
        Add a sending domain.

        The domain starts in ``draft``. There is NO verify call to make: toSend
        checks public DNS every 10 minutes and provisions the domain as soon as
        the records resolve.

        A duplicate raises a 409. Treat that as "already exists, go read it":
        domain names are globally unique, so a retry after a timeout hits this
        for a domain your first call created successfully.
        """
        return self._data(self._request("POST", "/v2/domains", {"name": name}))

    def get_domain(self, id: str) -> Dict[str, Any]:
        """
        Domain detail plus the DNS records your customer must publish.

        The DKIM key is unique to the team that owns the domain; do not reuse
        a value for another domain or team, it will not verify.
        """
        return self._data(self._request("GET", f"/v2/domains/{_segment(id)}"))

    def delete_domain(self, id: str) -> Dict[str, Any]:
        """
        Remove a domain. Does NOT touch your customer's DNS zone: records left
        published can let the domain be re-verified elsewhere.
        """
        return self._request("DELETE", f"/v2/domains/{_segment(id)}")

    # ── Email logs ──

    def list_emails(
        self,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
        status: Optional[str] = None,
        domain: Optional[str] = None,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Paginated delivery log. ``domain`` is a domain name or id; ``from_``
        and ``to`` are ISO 8601 date bounds.
        """
        return self._request("GET", "/v2/emails", query={
            "page": page, "per_page": per_page, "status": status, "domain": domain,
            "from": from_, "to": to, "search": search,
        })

    def get_email(self, message_id: str) -> Dict[str, Any]:
        """Look up one message by the message_id POST /v2/emails returned."""
        return self._data(self._request("GET", f"/v2/emails/{_segment(message_id)}"))

    # ── Suppressions ──

    def list_suppressions(
        self,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
        search: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._request("GET", "/v2/suppressions", query={
            "page": page, "per_page": per_page, "search": search, "status": status,
        })

    def delete_suppression(self, email: str) -> Dict[str, Any]:
        """
        Reactivate an address. Limited to 500 per day per account, shared with
        the dashboard; the response reports ``used_today``,
        ``remaining_today`` and ``daily_limit``.
        """
        return self._request("DELETE", "/v2/suppressions", query={"email": email})

    # ── Webhooks ──

    def list_webhooks(self, page: Optional[int] = None, per_page: Optional[int] = None) -> Dict[str, Any]:
        return self._request("GET", "/v2/webhooks", query={"page": page, "per_page": per_page})

    def create_webhook(
        self,
        url: str,
        events: List[str],
        title: Optional[str] = None,
        include_message: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        ``events`` accepts ``"bounced"`` and ``"complaint"``. The returned dict
        includes the signing ``secret``, generated by toSend and returned only
        in this response, so store it now.
        """
        payload: Dict[str, Any] = {"url": url, "events": events}
        if title is not None:
            payload["title"] = title
        if include_message is not None:
            payload["include_message"] = include_message
        return self._data(self._request("POST", "/v2/webhooks", payload))

    def update_webhook(self, id: int, **fields: Any) -> Dict[str, Any]:
        """Update any of ``title``, ``url``, ``events``, ``include_message``, ``status`` (active/inactive)."""
        return self._data(self._request("PUT", f"/v2/webhooks/{_segment(id)}", fields))

    def delete_webhook(self, id: int) -> Dict[str, Any]:
        return self._request("DELETE", f"/v2/webhooks/{_segment(id)}")

    # ── Sending API keys ──

    def list_sending_keys(self, page: Optional[int] = None, per_page: Optional[int] = None) -> Dict[str, Any]:
        """List sending keys, paginated. Keys come back masked."""
        return self._request("GET", "/v2/api-keys", query={"page": page, "per_page": per_page})

    def create_sending_key(self, name: str, domain: Optional[str] = None) -> Dict[str, Any]:
        """
        Mint a sending key for this team: how you give each client their own.

        The raw key (``api_key``) is in the response and nowhere else, ever.
        Pass ``domain`` (a domain id) to restrict it to one domain; omit it for
        all domains on the team. Needs the ``api_keys:write`` and
        ``emails:send`` scopes.
        """
        payload: Dict[str, Any] = {"name": name}
        if domain is not None:
            payload["domain"] = domain
        return self._data(self._request("POST", "/v2/api-keys", payload))

    def delete_sending_key(self, id: int) -> Dict[str, Any]:
        return self._request("DELETE", f"/v2/api-keys/{_segment(id)}")

    # ── Teams ──

    def list_teams(self) -> Dict[str, Any]:
        """
        Your account and its child teams. ``credit_balance`` on the account is
        the pooled figure; child teams draw on it and have no balance of their own.
        """
        return self._data(self._request("GET", "/v2/teams"))

    def create_team(self, name: str) -> Dict[str, Any]:
        """Only the parent account can create teams, so do not use for_account()."""
        return self._data(self._request("POST", "/v2/teams", {"name": name}))

    def update_team(self, id: int, name: Optional[str] = None, status: Optional[str] = None) -> Dict[str, Any]:
        """Rename a team and/or set ``status`` to ``"active"`` or ``"suspended"``."""
        payload: Dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if status is not None:
            payload["status"] = status
        return self._data(self._request("PUT", f"/v2/teams/{_segment(id)}", payload))
