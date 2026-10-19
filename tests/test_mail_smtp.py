"""The SMTP send path.

Email is the only way the owner finds out a booking happened, and the SMTP
route is the one he can turn on today with a Gmail app password — no new
provider account. These tests pin the parts that silently break delivery:
a missing HTML alternative, a skipped STARTTLS, or a From that does not match
the authenticated mailbox (which Gmail rewrites or rejects outright).

smtplib is stubbed rather than dialled, so this stays offline and sends
nothing. It verifies our side of the conversation, not Google's.
"""
import importlib, os, sys, unittest
from email.message import EmailMessage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "server"))


class FakeSMTP:
    """Records what notify.py would have said to a real server."""
    last = None

    def __init__(self, host, port, timeout=None):
        self.host, self.port, self.timeout = host, port, timeout
        self.started_tls = False
        self.login_args = None
        self.sent = None
        FakeSMTP.last = self

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def starttls(self, context=None):
        self.started_tls = True

    def login(self, user, password):
        self.login_args = (user, password)

    def send_message(self, msg):
        self.sent = msg


def load_notify(**env):
    """Re-import notify with mail env vars applied, since it reads them once."""
    for k in ("POSTMARK_TOKEN", "SMTP_HOST", "SMTP_PORT", "SMTP_USER",
              "SMTP_PASS", "MAIL_FROM", "OWNER_NOTIFY"):
        os.environ.pop(k, None)
    os.environ.update(env)
    import notify
    return importlib.reload(notify)


GMAIL = {
    "SMTP_HOST": "smtp.gmail.com",
    "SMTP_PORT": "587",
    "SMTP_USER": "natejennings99@gmail.com",
    "SMTP_PASS": "app-password-not-real",
    "MAIL_FROM": "natejennings99@gmail.com",
}


class SmtpSendTest(unittest.TestCase):
    def setUp(self):
        self.notify = load_notify(**GMAIL)
        self.notify.smtplib.SMTP = FakeSMTP
        FakeSMTP.last = None

    def tearDown(self):
        load_notify()          # leave the module unconfigured for other tests

    def test_gmail_settings_count_as_configured(self):
        self.assertTrue(self.notify.configured())
        self.assertEqual(self.notify.provider(), "smtp")

    def test_send_reports_success_and_dials_the_right_host(self):
        ok = self.notify.send("guest@example.com", "Subj", "text body",
                              "<p>html body</p>")
        self.assertTrue(ok)
        s = FakeSMTP.last
        self.assertIsNotNone(s, "send() never opened an SMTP connection")
        self.assertEqual((s.host, s.port), ("smtp.gmail.com", 587))

    def test_starttls_before_login(self):
        """Without STARTTLS, Gmail rejects the login and the password would
        have crossed the wire in the clear."""
        self.notify.send("guest@example.com", "Subj", "t", "<p>h</p>")
        s = FakeSMTP.last
        self.assertTrue(s.started_tls)
        self.assertEqual(s.login_args[0], "natejennings99@gmail.com")

    def test_message_carries_both_text_and_html(self):
        self.notify.send("guest@example.com", "Your cleaning is booked",
                         "text body", "<p>html body</p>")
        msg = FakeSMTP.last.sent
        self.assertIsInstance(msg, EmailMessage)
        self.assertEqual(msg["To"], "guest@example.com")
        self.assertEqual(msg["Subject"], "Your cleaning is booked")
        types = sorted(p.get_content_type() for p in msg.walk()
                       if not p.is_multipart())
        self.assertEqual(types, ["text/html", "text/plain"])

    def test_from_matches_the_authenticated_mailbox(self):
        """Gmail only lets you send as the account you logged in with, or a
        verified alias. A mismatch here is the classic silent-failure setup."""
        self.notify.send("guest@example.com", "Subj", "t", "<p>h</p>")
        self.assertEqual(FakeSMTP.last.sent["From"], os.environ["SMTP_USER"])

    def test_a_broken_server_never_breaks_the_booking(self):
        class Exploding(FakeSMTP):
            def send_message(self, msg):
                raise OSError("connection reset")

        self.notify.smtplib.SMTP = Exploding
        self.assertFalse(
            self.notify.send("guest@example.com", "Subj", "t", "<p>h</p>"),
            "a failed send must report False, not raise",
        )


class UnconfiguredTest(unittest.TestCase):
    def test_no_env_means_not_configured(self):
        n = load_notify()
        self.assertFalse(n.configured())
        self.assertEqual(n.provider(), "none")
        self.assertFalse(n.send("a@b.com", "s", "t", "<p>h</p>"))


if __name__ == "__main__":
    unittest.main()
