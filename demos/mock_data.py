"""Synthetic GitHub data (PRs, unified diffs, review threads) for demo
recordings. Everything here is fabricated so the demo is deterministic and
never touches the GitHub API.
"""

from gitkeeper.github.client import (
    PullRequestData,
    PullRequestFile,
    ReviewRecord,
    ReviewerRequest,
    ReviewThread,
    ThreadComment,
)

VIEWER = "octocat"


def _file(path: str, additions: int, deletions: int) -> PullRequestFile:
    return PullRequestFile(
        path=path,
        additions=additions,
        deletions=deletions,
        change_type="ADDED" if additions and not deletions else "MODIFIED",
    )


def _reviewer(reviewer: str) -> ReviewerRequest:
    return ReviewerRequest(reviewer, is_team=False)


def _team(team: str) -> ReviewerRequest:
    return ReviewerRequest(team, is_team=True)


def _approved(author: str, when: str = "2026-07-20T10:00:00Z") -> ReviewRecord:
    return ReviewRecord(author=author, state="APPROVED", submitted_at=when)


def _changes_requested(author: str, when: str = "2026-07-21T10:00:00Z") -> ReviewRecord:
    return ReviewRecord(author=author, state="CHANGES_REQUESTED", submitted_at=when)


def _dismissed(author: str, when: str = "2026-07-21T10:00:00Z") -> ReviewRecord:
    return ReviewRecord(author=author, state="DISMISSED", submitted_at=when)


def _pr(
    number: int,
    title: str,
    repo: str,
    author: str,
    updated_at: str,
    additions: int,
    deletions: int,
    changed_files: int,
    body: str,
    reviewers: list,
    reviews: list,
    files: list,
    pushed_at: str | None = "2026-07-28T10:10:00Z",
    base_ref: str = "main",
    head_ref: str = "feature",
    ci: str = "SUCCESS",
) -> PullRequestData:
    return PullRequestData(
        id=f"PR_{number}",
        number=number,
        title=title,
        body=body,
        url=f"https://github.com/{repo}/pull/{number}",
        repo_name_with_owner=repo,
        author=author,
        is_draft=False,
        state="OPEN",
        created_at="2026-07-01T09:00:00Z",
        updated_at=updated_at,
        additions=additions,
        deletions=deletions,
        changed_files_count=changed_files,
        ci_status=ci,
        pushed_at=pushed_at,
        base_ref=base_ref,
        head_ref=head_ref,
        requested_reviewers=reviewers,
        reviews=reviews,
        files=files,
    )


def build_prs() -> list[PullRequestData]:
    """Return the fabricated review-request queue."""
    return [
        _pr(
            884,
            "fix: verify JWT algorithm before trusting session",
            "acme/backend",
            "alice",
            "2026-07-28T10:24:00Z",
            134,
            23,
            7,
            "## Summary\n\nTightens token verification so the decoder never\n"
            "silently trusts a forged `alg` header.\n\n## Changes\n\n"
            "- Check `alg` after decoding the header\n"
            "- Fail loudly on non-RS256 tokens\n"
            "- Scope-check the verified payload\n",
            [_team("core-service"), _reviewer("bob"), _reviewer("lea")],
            [_approved("bob"), _changes_requested("lea")],
            [
                _file("src/auth/jwt.py", 62, 10),
                _file("src/auth/keys.py", 14, 0),
                _file("src/auth/token.py", 18, 3),
                _file("tests/test_jwt.py", 22, 4),
                _file("tests/test_keys.py", 8, 0),
                _file("migrations/0008_token_claims.py", 5, 0),
            ],
            pushed_at="2026-07-28T10:10:00Z",
            head_ref="fix/jwt-alg-check",
        ),
        _pr(
            936,
            "feat: add idempotency keys to payment intents",
            "acme/checkout",
            "lea",
            "2026-07-27T16:02:00Z",
            74,
            6,
            3,
            "## What\n\nGuards payment creation with an idempotency key so retries\n"
            "cannot double-charge customers.\n\n## Notes\n\n- Key set once per intent\n",
            [_reviewer("bob"), _reviewer("sam")],
            [_approved("bob"), _changes_requested(VIEWER, "2026-07-26T09:00:00Z")],
            [
                _file("src/payments/intents.py", 41, 6),
                _file("src/payments/keys.py", 14, 0),
                _file("tests/test_intents.py", 19, 0),
            ],
            pushed_at="2026-07-25T14:00:00Z",
            head_ref="feat/idempotency-keys",
        ),
        _pr(
            779,
            "fix: retry stale webhook deliveries with backoff",
            "acme/webhooks",
            "bob",
            "2026-07-26T11:30:00Z",
            41,
            9,
            3,
            "Webhook deliveries fan out more than once when the worker\n"
            "pool restarts mid-batch. Adds an at-least-once queue.\n",
            [_reviewer("lea"), _reviewer("frida")],
            [_changes_requested("octocat", "2026-07-22T08:00:00Z")],
            [
                _file("src/deliver/queue.py", 21, 4),
                _file("src/deliver/backoff.py", 14, 0),
                _file("tests/test_deliver.py", 6, 5),
            ],
            pushed_at="2026-07-21T15:00:00Z",
            head_ref="fix/webhook-backoff",
        ),
        _pr(
            620,
            "feat: scope audit-log exports to one tenant",
            "acme/checkout",
            "sam",
            "2026-07-25T15:40:00Z",
            30,
            2,
            1,
            "Adds a tenant-id filter to the audit export endpoint.\n",
            [_reviewer("octocat")],
            [_approved("mona", "2026-07-23T12:00:00Z")],
            [_file("src/exports/audit.py", 30, 2)],
            pushed_at="2026-07-25T15:20:00Z",
            head_ref="feat/tenant-filter",
        ),
        _pr(
            418,
            "fix: normalize currency codes before rounding",
            "acme/checkout",
            "frida",
            "2026-07-24T09:15:00Z",
            41,
            4,
            2,
            "Normalizes mixed-case currency codes before any rounding.\n",
            [_reviewer("octocat"), _reviewer("monica")],
            [],
            [
                _file("src/fx/currency.py", 21, 2),
                _file("tests/test_currency.py", 20, 2),
            ],
            pushed_at="2026-07-24T09:00:00Z",
            head_ref="fix/normalize-currency",
        ),
        _pr(
            101,
            "chore: drop deprecated webhook signature v2",
            "acme/webhooks",
            "vishal",
            "2026-07-23T08:55:00Z",
            54,
            41,
            2,
            "Removes the v2 signing scheme, three releases after deprecation.\n",
            [],
            [_approved("frida"), _approved("octocat", "2026-07-22T11:00:00Z")],
            [
                _added("src/sign/ed25519.py", 44, 11),
                _deleted("src/sign/hmac.py", 10, 30),
            ],
            pushed_at="2026-07-23T08:40:00Z",
            head_ref="chore/drop-sign-v2",
        ),
    ]


def _added(path: str, additions: int, deletions: int) -> PullRequestFile:
    return PullRequestFile(path=path, additions=additions, deletions=deletions, change_type="ADDED")


def _deleted(path: str, additions: int, deletions: int) -> PullRequestFile:
    return PullRequestFile(path=path, additions=additions, deletions=deletions, change_type="DELETED")


# --------------------------------------------------------------------------
# One fabricated unified diff per pull request. The first file in each string
# is the one the file tree highlights when the PR is opened.
# --------------------------------------------------------------------------

BACKEND_884_DIFF = """diff --git a/src/auth/jwt.py b/src/auth/jwt.py
--- a/src/auth/jwt.py
+++ b/src/auth/jwt.py
@@ -17,11 +17,15 @@
 class TokenDecoder:
     def __init__(self, keys: KeyStore):
         self._keys = keys

     def verify(self, token: str) -> dict:
         header = decode_header(token)
-            raise UnsupportedAlgorithm(token)
-            key = lookup_key(header["kid"])
-            return verify_payload(token, key)
-            return {}
+            algorithm = header.get("alg", "")
+            if algorithm != "RS256":
+                raise TokenError(algorithm)
+            key = lookup_key(header["kid"])
+            payload = verify_payload(token, key)
+            if payload.get("scope") != "*":
+                raise ScopeError(payload)
+            return payload

diff --git a/src/auth/keys.py b/src/auth/keys.py
new file mode 100644
--- /dev/null
+++ b/src/auth/keys.py
@@ -0,0 +1,7 @@
+
+class KeyStore:
+    def __init__(self, keys: dict[str, bytes]) -> None:
+        self._keys = keys
+
+    def public_for_kid(self, kid: str) -> bytes:
+        return self._keys[kid]
+
+    def validate(self, kid: str) -> bool:
+        return kid in self._keys
diff --git a/src/auth/token.py b/src/auth/token.py
--- a/src/auth/token.py
+++ b/src/auth/token.py
@@ -2,5 +2,9 @@
 from __future__ import annotations
 
 def issue_access_token(claims: dict) -> str:
-    return _sign(claims, expires=1_200)
-    return _sign(claims, ttl=3_600)
+    from_cache = _get_cached(hash(claims))
+    if from_cache:
+        return from_cache
+    token = _sign(claims, ttl=3_600)
+    _set_cached(hash(claims), token)
+    return token
diff --git a/tests/test_jwt.py b/tests/test_jwt.py
--- a/tests/test_jwt.py
+++ b/tests/test_jwt.py
@@ -1,5 +1,7 @@
 
 def test_valid_token_round_trips():
     raw = issue_access_token({"role": "admin"})
-    assert raw.count(".") == 2
-    assert raw.startswith("ey")
+    claims = decode(raw)
+    assert claims["role"] == "admin"
+    assert claims["aud"] == "gitkeeper"
+    assert raw.count(".") == 2
diff --git a/tests/test_keys.py b/tests/test_keys.py
new file mode 100644
--- /dev/null
+++ b/tests/test_keys.py
@@ -0,0 +1,6 @@
+
+def test_key_rotation():
+    store = KeyStore({"kid-1": b"pub"})
+    assert store.public_for_kid("kid-1") == b"pub"
+    assert not store.validate("kid-2")
"""

CHECKOUT_936_DIFF = """diff --git a/src/payments/intents.py b/src/payments/intents.py
--- a/src/payments/intents.py
+++ b/src/payments/intents.py
@@ -5,6 +5,7 @@
 from payments.gateway import Gateway

 def create_intent(customer_id, amount, idem_key):
-    return gateway.charge(customer_id, amount)
+    pending = gateway.pending(idem_key)
+    if pending:
+        return pending
+    return gateway.charge(customer_id, amount, key=idem_key)
diff --git a/src/payments/keys.py b/src/payments/keys.py
new file mode 100644
--- /dev/null
+++ b/src/payments/keys.py
@@ -0,0 +1,4 @@
+
+def idempotency_key(customer_id, fingerprint):
+    return f"{customer_id}:{fingerprint}"
"""

WEBHOOKS_779_DIFF = """diff --git a/src/deliver/queue.py b/src/deliver/queue.py
--- a/src/deliver/queue.py
+++ b/src/deliver/queue.py
@@ -3,6 +3,7 @@
 from dataclasses import dataclass
 
-@dataclass
-class DeliveryQueue:
-    def enqueue(self, job):
-        return self._store.append(job)
+class DeliveryQueue:
+    def __init__(self, store):
+        self._store = store
+
+    def enqueue(self, job):
+        self._store.append(job)

diff --git a/src/deliver/backoff.py b/src/deliver/backoff.py
new file mode 100644
--- /dev/null
+++ b/src/deliver/backoff.py
@@ -0,0 +1,6 @@
+import time
+
+def next_delay(attempt, base=5):
+    return base * 2 ** min(attempt, 6)
"""

CHECKOUT_620_DIFF = """diff --git a/src/exports/audit.py b/src/exports/audit.py
--- a/src/exports/audit.py
+++ b/src/exports/audit.py
@@ -2,4 +2,5 @@
 def export_audit_log(tenant_ids=None, since=None):
-    rows = query_all()
-    return render(rows)
+    rows = query_all(tenant_ids=tenant_ids, since=since)
+    return render_csv(rows)
+    return render_json(rows) if rows.raw else render_csv(rows)
"""

CHECKOUT_418_DIFF = """diff --git a/src/fx/currency.py b/src/fx/currency.py
--- a/src/fx/currency.py
+++ b/src/fx/currency.py
@@ -1,4 +1,5 @@
 def round_for_currency(amount, code):
-    scale = SCALES[code.upper()]
-    return Decimal(amount).quantize(scale)
+    scale = SCALES.get(code.upper())
+    if scale is None:
+        raise UnknownCurrency(code)
+    return Decimal(amount).quantize(scale)
diff --git a/tests/test_currency.py b/tests/test_currency.py
--- a/tests/test_currency.py
+++ b/tests/test_currency.py
@@ -1,3 +1,4 @@
 def test_normalizes_case():
-    assert round_for_currency("9.995", "usd") == 9.99
+    assert round_for_currency("9.995", "USD") == Decimal("9.99")
"""

WEBHOOKS_101_DIFF = """diff --git a/src/sign/hmac.py b/src/sign/hmac.py
deleted file mode 100644
--- a/src/sign/hmac.py
+++ /dev/null
@@ -1,8 +0,0 @@
-import hashlib
-import hmac as _hmac
-
-def sign(payload, key):
-    return _hmac.new(key, payload, hashlib.sha256).hexdigest()
diff --git a/src/sign/ed25519.py b/src/sign/ed25519.py
--- a/src/sign/ed25519.py
+++ b/src/sign/ed25519.py
@@ -1,4 +1,6 @@
 def verify(payload, expected):
-    return sig.verify(payload, expected)
+    return sig.verify(payload, expected, ctx=b"gitkeeper-v2")
"""

DIFFS = {
    "acme/backend#884": BACKEND_884_DIFF,
    "acme/checkout#936": CHECKOUT_936_DIFF,
   "acme/webhooks#779": WEBHOOKS_779_DIFF,
    "acme/checkout#620": CHECKOUT_620_DIFF,
    "acme/checkout#418": CHECKOUT_418_DIFF,
    "acme/webhooks#101": WEBHOOKS_101_DIFF,
}


def build_threads() -> dict[str, list[ReviewThread]]:
    return {
        "acme/backend#884": [
            ReviewThread(
                path="src/auth/jwt.py",
                line=29,
                comments=[
                    ThreadComment(author="bob", body="Good catch — alg was trusted"),
                    ThreadComment(author="lea", body="Should we allow ES256?"),
                ],
            ),
        ],
        "acme/checkout#936": [
            ReviewThread(
                path="src/payments/intents.py",
                line=6,
                comments=[
                    ThreadComment(author="sam", body="Key must be stored before mutating"),
                ],
            ),
        ],
    }