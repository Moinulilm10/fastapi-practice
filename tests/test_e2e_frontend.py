"""End-to-end browser tests for the Streamlit frontend.

These tests exercise the real user journey against the app stack:

1. the FastAPI API runs on http://127.0.0.1:8000
2. the Streamlit frontend runs on http://127.0.0.1:8501
3. a human can create an account, sign in, and browse the feed

Run the stack before executing this file:

    docker compose up --build -d db api frontend
    uv run pytest tests/test_e2e_frontend.py -m e2e
"""

from __future__ import annotations

import uuid

import pytest
from playwright.sync_api import Page, expect

STREAMLIT_URL = "http://127.0.0.1:8501"


@pytest.mark.e2e
def test_user_can_register_and_sign_in(page: Page):
    """Create a new account, confirm the UI accepts it, and reach the feed."""
    email = f"e2e-{uuid.uuid4()}@example.com"
    password = "StrongPassword123!"

    # The Streamlit app renders its auth flow on first load.
    page.goto(STREAMLIT_URL, wait_until="networkidle")
    expect(page.get_by_text("Welcome back.")).to_be_visible(timeout=15_000)

    # There are two matching input pairs before registration: one hidden sign-in form
    # and one visible registration form. Select the actual text/password inputs by
    # type so the test does not interact with the password visibility button.
    page.get_by_role("tab", name="Create account").click()
    page.locator("input[type='text'][aria-label='Email']").last.fill(email)
    page.locator("input[type='password'][aria-label='Password']").last.fill(password)
    page.get_by_role("button", name="Create account").click()

    # The app signs the user in immediately after successful registration, then the
    # dashboard should show the authenticated feed and the signed-in user email.
    expect(page.get_by_text("The feed")).to_be_visible(timeout=20_000)
    expect(page.get_by_text(email)).to_be_visible(timeout=20_000)


@pytest.mark.e2e
def test_signed_in_user_can_sign_out(page: Page):
    """A signed-in user should be able to sign out and return to the auth screen."""
    email = f"e2e-{uuid.uuid4()}@example.com"
    password = "AnotherStrongPassword456!"

    page.goto(STREAMLIT_URL, wait_until="networkidle")
    page.get_by_role("tab", name="Create account").click()
    page.locator("input[type='text'][aria-label='Email']").last.fill(email)
    page.locator("input[type='password'][aria-label='Password']").last.fill(password)
    page.get_by_role("button", name="Create account").click()

    expect(page.get_by_text("The feed")).to_be_visible(timeout=20_000)

    # Sign-out is a user-visible action exposed in the sidebar navigation.
    page.get_by_role("button", name="Sign out").click()
    expect(page.get_by_text("Welcome back.")).to_be_visible(timeout=15_000)
