from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest
from playwright.sync_api import sync_playwright


MOBILE_WIDTH = 390
MOBILE_HEIGHT = 844


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _browser_executable() -> str:
    candidates = (
        os.getenv("CHROMIUM_PATH"),
        shutil.which("google-chrome"),
        shutil.which("google-chrome-stable"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
    )
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return str(candidate)
    pytest.fail("A Chromium/Chrome executable is required for the 390x844 browser QA gate")


def _wait_for_server(base_url: str, process: subprocess.Popen[str]) -> None:
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout else ""
            pytest.fail(f"Vexmera test server exited early:\n{output}")
        try:
            response = httpx.get(f"{base_url}/health", timeout=1.0)
            if response.status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.2)
    pytest.fail("Vexmera test server did not become ready")


def _assert_no_page_overflow(page) -> None:
    metrics = page.evaluate(
        """() => ({
          innerWidth: window.innerWidth,
          innerHeight: window.innerHeight,
          bodyWidth: document.body.scrollWidth,
          rootWidth: document.documentElement.scrollWidth
        })"""
    )
    assert metrics["innerWidth"] == MOBILE_WIDTH
    assert metrics["innerHeight"] == MOBILE_HEIGHT
    assert metrics["bodyWidth"] <= MOBILE_WIDTH + 1, metrics
    assert metrics["rootWidth"] <= MOBILE_WIDTH + 1, metrics


def test_authenticated_mobile_viewport_390x844(tmp_path: Path) -> None:
    """Prove the authenticated app works in a real Chromium 390x844 viewport.

    This is deliberately browser-level evidence rather than a CSS source audit.
    It verifies the unauthenticated shell at the target width, establishes a
    synthetic same-origin session through the real auth API, completes onboarding,
    checks the actual responsive menu, traverses every primary view and fails if
    the page develops horizontal overflow. No external providers, Stripe, ads,
    budgets, bids or live services are touched.
    """

    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"
    env = os.environ.copy()
    env.update(
        {
            "VEZMORA_DB_PATH": str(tmp_path / "mobile-browser.db"),
            "VEZMORA_DATA_DIR": str(tmp_path),
            "VEZMORA_APP_URL": base_url,
            "VEZMORA_COOKIE_SECURE": "false",
            "VEZMORA_SERVERLESS": "true",
            "SCHEDULER_ENABLED": "false",
            "WORKER_ENABLED": "false",
            "AUTOPILOT_EXECUTION_ENABLED": "false",
            "EXECUTION_ENABLED": "false",
        }
    )
    for key in (
        "DATABASE_URL",
        "POSTGRES_URL",
        "TURSO_DATABASE_URL",
        "TURSO_AUTH_TOKEN",
        "OPENAI_API_KEY",
        "STRIPE_SECRET_KEY",
        "STRIPE_WEBHOOK_SECRET",
    ):
        env.pop(key, None)

    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        _wait_for_server(base_url, process)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=_browser_executable(),
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            context = browser.new_context(
                viewport={"width": MOBILE_WIDTH, "height": MOBILE_HEIGHT},
                device_scale_factor=1,
                is_mobile=True,
                has_touch=True,
            )
            page = context.new_page()
            page.goto(f"{base_url}/app", wait_until="networkidle")

            consent = page.locator('[data-consent="denied"]')
            if consent.is_visible():
                consent.click()
            assert page.locator("#authScreen").is_visible()
            assert page.locator("#appShell").is_hidden()
            _assert_no_page_overflow(page)

            registration = page.evaluate(
                """async (payload) => {
                  const response = await fetch('/api/auth/register', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                  });
                  return {status: response.status, body: await response.json()};
                }""",
                {
                    "email": "mobile-browser-qa@example.com",
                    "password": "VexmeraMobileQA-2026!",
                    "workspace_name": "Vexmera Mobile QA",
                },
            )
            assert registration["status"] == 200, registration
            workspace_id = int(registration["body"]["workspace_id"])

            onboarding = {
                "company_name": "Vexmera Mobile QA",
                "industry": "Software",
                "market": "Sweden",
                "website": "https://example.com",
                "audience": "Small businesses",
                "offer": "QA test service",
                "brand_voice": "clear, trustworthy, useful",
                "language": "sv",
                "primary_goal": "sales",
                "monthly_budget": 1000,
                "primary_channels": ["organic", "email"],
                "growth_target": "+10% test target",
                "biggest_marketing_problem": "Test-only mobile QA workflow",
                "timezone": "Europe/Stockholm",
                "team_size": 1,
            }
            completed = page.evaluate(
                """async ({workspaceId, payload}) => {
                  const response = await fetch(`/api/onboarding/complete?workspace_id=${workspaceId}`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                  });
                  return {status: response.status, body: await response.json()};
                }""",
                {"workspaceId": workspace_id, "payload": onboarding},
            )
            assert completed["status"] == 200, completed

            page.reload(wait_until="networkidle")
            page.locator("#appShell").wait_for(state="visible")
            _assert_no_page_overflow(page)

            menu = page.locator("#appMenuToggle")
            nav = page.locator("#appNavigation")
            assert menu.is_visible()
            assert menu.get_attribute("aria-expanded") == "false"
            assert not nav.is_visible()

            menu.click()
            assert menu.get_attribute("aria-expanded") == "true"
            assert nav.is_visible()
            assert page.locator(".sidebar").evaluate("el => el.classList.contains('mobile-nav-open')") is True
            _assert_no_page_overflow(page)

            views = [
                "dashboard",
                "agent",
                "strategy",
                "campaign",
                "brief",
                "queue",
                "autopilot",
                "rivals",
                "connect",
                "insights",
                "team",
                "profile",
            ]
            for view in views:
                if not nav.is_visible():
                    menu.click()
                button = page.locator(f'.nav[data-view="{view}"]')
                button.click()
                page.locator(f"#{view}").wait_for(state="visible")
                _assert_no_page_overflow(page)

            if not nav.is_visible():
                menu.click()
            page.locator('.nav[data-view="team"]').click()
            page.locator("#team").wait_for(state="visible")
            delete_prepare = page.locator("#accountDeletePrepare")
            delete_prepare.wait_for(state="visible")
            delete_prepare.click()
            page.wait_for_timeout(250)
            _assert_no_page_overflow(page)

            context.close()
            browser.close()
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
