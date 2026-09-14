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


def test_google_production_access_matches_current_verified_evidence():
    checklist = _read("DEPLOY_CHECKLIST.md")
    launch_plan = _read("LAUNCH_GAP_PLAN.md")

    assert "Manager-to-client relationship accepted and active" in checklist
    assert "Explorer Access approved 2026-09-12" in checklist
    assert "Complete Google Ads sync against the real linked account" in checklist
    assert "Basic Access is a future scaling/functionality upgrade" in launch_plan
    assert "Basic Access approval still requires external verification" not in launch_plan


def test_launch_plan_keeps_remaining_manual_gates_explicit():
    launch_plan = _read("LAUNCH_GAP_PLAN.md").lower()

    for required_gate in (
        "fresh green ci",
        "billing portal configuration",
        "authenticated desktop and mobile browser qa",
        "legal entity",
        "legal review",
    ):
        assert required_gate in launch_plan


def test_launch_plan_does_not_reopen_completed_observability_or_google_gates():
    launch_plan = _read("LAUNCH_GAP_PLAN.md").lower()

    assert "direct vercel project/runtime inspection is working again" in launch_plan
    assert "explorer access" in launch_plan
    assert "real production google ads read-only sync" in launch_plan
    assert "direct chatgpt to vercel production runtime/log inspection remains unavailable" not in launch_plan
