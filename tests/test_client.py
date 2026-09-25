"""Tests for the ToSend Python SDK. Run: python3 -m unittest discover -s tests"""

import io
import json
import os
import sys
import unittest
from unittest import mock
from urllib.error import HTTPError
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tosend import ToSend, ToSendAdmin, ToSendError  # noqa: E402

ADMIN_KEY = "tsend_admin_0123456789abcdef0123456789abcdef"


class FakeResponse:
    def __init__(self, body):
        self._body = json.dumps(body).encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def reply(body):
    """Patch urlopen to answer with `body`; returns the mock to inspect calls."""
    return mock.patch("tosend.client.urlopen", return_value=FakeResponse(body))


def fail(status, body):
    err = HTTPError("https://api.tosend.com", status, "error", {}, io.BytesIO(json.dumps(body).encode("utf-8")))
    return mock.patch("tosend.client.urlopen", side_effect=err)


def sent_request(m):
    return m.call_args[0][0]


class AdminKeyTests(unittest.TestCase):
    def test_rejects_a_sending_key(self):
        with self.assertRaises(ToSendError) as ctx:
            ToSendAdmin("tsend_0123456789abcdef")
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertIn("tsend_admin_", ctx.exception.message)

    def test_rejects_an_empty_key(self):
        with self.assertRaises(ToSendError):
            ToSendAdmin("  ")

    def test_for_account_sends_header_and_leaves_base_untouched(self):
        admin = ToSendAdmin(ADMIN_KEY)
        child = admin.for_account(4203)

        with reply({"data": []}) as m:
            child.list_domains()
            self.assertEqual(sent_request(m).get_header("X-account-id"), "4203")

        with reply({"data": []}) as m:
            admin.list_domains()
            self.assertIsNone(sent_request(m).get_header("X-account-id"))

    def test_list_sending_keys_pages(self):
        with reply({"data": [], "total": 0, "page": 2, "per_page": 50}) as m:
            result = ToSendAdmin(ADMIN_KEY).list_sending_keys(page=2, per_page=50)

        query = parse_qs(urlparse(sent_request(m).full_url).query)
        self.assertEqual(query, {"page": ["2"], "per_page": ["50"]})
        self.assertEqual(result["page"], 2)

    def test_delete_suppression_encodes_the_email(self):
        with reply({"deleted": True, "remaining_today": 499}) as m:
            result = ToSendAdmin(ADMIN_KEY).delete_suppression("a+b@x.com")

        req = sent_request(m)
        self.assertEqual(req.get_method(), "DELETE")
        self.assertIsNone(req.data)
        self.assertIn("email=a%2Bb%40x.com", req.full_url)
        self.assertEqual(parse_qs(urlparse(req.full_url).query)["email"], ["a+b@x.com"])
        self.assertEqual(result["remaining_today"], 499)

    def test_path_ids_cannot_escape_the_path(self):
        with reply({"data": {}}) as m:
            ToSendAdmin(ADMIN_KEY).get_domain("../teams")
        self.assertTrue(sent_request(m).full_url.endswith("/v2/domains/..%2Fteams"))

    def test_single_resource_calls_unwrap_data(self):
        with reply({"data": {"id": 9, "name": "Acme", "status": "active"}}):
            self.assertEqual(ToSendAdmin(ADMIN_KEY).create_team("Acme")["id"], 9)

    def test_list_emails_maps_from_(self):
        with reply({"data": []}) as m:
            ToSendAdmin(ADMIN_KEY).list_emails(from_="2026-09-01", status="sent")
        query = parse_qs(urlparse(sent_request(m).full_url).query)
        self.assertEqual(query, {"from": ["2026-09-01"], "status": ["sent"]})


class ErrorDecodingTests(unittest.TestCase):
    def test_flat_admin_error_exposes_the_code(self):
        body = {
            "status_code": 403,
            "message": "This admin key does not have the domains:read scope.",
            "errors": {"code": "insufficient_scope", "required_scope": "domains:read"},
        }
        with fail(403, body):
            with self.assertRaises(ToSendError) as ctx:
                ToSendAdmin(ADMIN_KEY).list_domains()

        err = ctx.exception
        self.assertEqual(err.status_code, 403)
        self.assertEqual(err.code, "insufficient_scope")
        self.assertEqual(err.errors["required_scope"], "domains:read")
        self.assertEqual(err.error_type, "unknown_error")

    def test_nested_sending_error(self):
        body = {
            "status_code": 422,
            "error_type": "validation_error",
            "message": "Subject is required.",
            "errors": {"subject": {"required": "Subject is required."}},
        }
        with fail(422, body):
            with self.assertRaises(ToSendError) as ctx:
                ToSend("tsend_abc").send(from_address={"email": "a@b.com"}, to=[{"email": "c@d.com"}], subject="")

        err = ctx.exception
        self.assertTrue(err.is_validation_error)
        self.assertEqual(err.errors["subject"]["required"], "Subject is required.")
        self.assertIsNone(err.code)

    def test_status_comes_from_http_when_body_lacks_it(self):
        with fail(429, {"message": "Too many requests."}):
            with self.assertRaises(ToSendError) as ctx:
                ToSendAdmin(ADMIN_KEY).create_domain("x.com")
        self.assertEqual(ctx.exception.status_code, 429)
        self.assertTrue(ctx.exception.is_rate_limit_error)


class AccountInfoTests(unittest.TestCase):
    def test_decodes_the_real_shape(self):
        body = {
            "account": {
                "id": 142, "status": "active", "plan_type": "pro", "credit_balance": 48750,
                "monthly_email_limit": 100000, "limit_per_second": 14, "ses_region": "us-east-1",
                "bounce_rate": 0.012, "complaint_rate": 0.0003, "ses_status": "healthy",
            },
            "domains": [{
                "id": 88, "domain_name": "acme.com", "verification_status": "verified",
                "is_default": 1, "total_sent": 24189, "total_bounced": 212, "total_complained": 7,
            }],
        }
        with reply(body):
            info = ToSend("tsend_abc").get_account_info()

        self.assertEqual(info.account.id, 142)
        self.assertEqual(info.account.credit_balance, 48750)
        self.assertEqual(info.account.limit_per_second, 14)
        self.assertAlmostEqual(info.account.bounce_rate, 0.012)
        self.assertEqual(info.domains[0].id, 88)
        self.assertIs(info.domains[0].is_default, True)
        self.assertEqual(info.domains[0].total_sent, 24189)

    def test_null_credit_balance_means_unlimited(self):
        with reply({"account": {"id": 1, "credit_balance": None}, "domains": []}):
            info = ToSend("tsend_abc").get_account_info()
        self.assertIsNone(info.account.credit_balance)


if __name__ == "__main__":
    unittest.main()


class UserAgentTest(unittest.TestCase):
    """Python-urllib's default agent is blocked by Cloudflare (403, error 1010)."""

    def test_every_request_sends_the_sdk_user_agent(self):
        from tosend.client import USER_AGENT
        for client in (ToSend("tsend_x"), ToSendAdmin("tsend_admin_x")):
            with mock.patch("tosend.client.urlopen") as op:
                op.return_value.__enter__.return_value.read.return_value = b"{}"
                (client.get_account_info if isinstance(client, ToSend) else client.get_info)()
                req = op.call_args[0][0]
                self.assertEqual(req.get_header("User-agent"), USER_AGENT)
                self.assertTrue(USER_AGENT.startswith("tosend-python/"))
