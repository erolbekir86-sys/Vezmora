from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_operational_docs_use_current_stripe_environment_names():
    docs = "\n".join(
        _read(name)
        for name in (
            ".env.example",
            "PRODUCTION_ENVIRONMENT.md",
            "DEPLOY_CHECKLIST.md",
            "README.md",
        )
    )

    assert "STRIPE_PRICE_START" in docs
    assert "STRIPE_PRICE_GROWTH" in docs
    assert "STRIPE_PRICE_PRO" in docs
    assert "STRIPE_PRICE_STARTER" not in docs
    assert "STRIPE_PRICE_SCALE" not in docs


def test_launch_docs_keep_current_pricing_gate_explicit():
    docs = "\n".join(
        _read(name)
        for name in (
            "PRODUCTION_ENVIRONMENT.md",
            "DEPLOY_CHECKLIST.md",
            "LAUNCH_GAP_PLAN.md",
        )
    )

    assert "995" in docs
    assert "1,495" in docs
    assert "2,995" in docs
    assert "VEZMORA_STRIPE_PRICING_VERSION" in docs
    assert "2026-09-start-growth-pro" in docs


def test_google_manager_link_is_not_listed_as_pending_work():
    checklist = _read("DEPLOY_CHECKLIST.md")
    launch_plan = _read("LAUNCH_GAP_PLAN.md")

    assert "Accept the pending manager-account link request" not in checklist
    assert "Manager-to-client relationship accepted and active" in checklist
    assert "manager-to-client relationship is accepted and active" in launch_plan
    assert "Receive Google approval for Basic Access" in checklist


def test_launch_plan_keeps_external_gates_distinct_from_completed_code():
    launch_plan = _read("LAUNCH_GAP_PLAN.md")

    for required_gate in (
        "direct Vercel",
        "Google Ads Basic Access",
        "Stripe sandbox",
        "authenticated browser QA",
        "legal sign-off",
    ):
        assert required_gate.lower() in launch_plan.lower()
