from .production_env_guards import apply_production_env_guards as _apply_production_env_guards

# Production safety overrides must run before app.main is imported because
# some beta-only behavior is selected from environment flags at import time.
_apply_production_env_guards()

# Install KPI semantic translation before app.main/core/brief modules import
# store helpers. This keeps historical GA sessions out of paid-click metrics
# without a risky production data migration.
from .kpi_semantics import install_kpi_semantics_guard as _install_kpi_semantics_guard
_install_kpi_semantics_guard()

# Password-reset and workspace-invite tokens are one-time capabilities. Install
# atomic claim helpers before app.main binds the store functions so concurrent
# requests cannot both accept the same token.
from .one_time_token_safety import install_one_time_token_safety as _install_one_time_token_safety
_install_one_time_token_safety()

# Expired sessions, reset tokens and workspace invites no longer need to remain
# in capability tables. Prune expired rows opportunistically when new entries of
# the same type are issued, before auth/main bind creation helpers.
from .capability_retention import install_capability_retention as _install_capability_retention
_install_capability_retention()

# OAuth state is also a one-time capability. Consume it with one atomic database
# statement before connector modules bind the helper so concurrent callbacks
# cannot reuse the same Google/Meta state value.
from .oauth_state_safety import install_oauth_state_safety as _install_oauth_state_safety
_install_oauth_state_safety()

# Jobs and queued transactional emails must also be claimed once. SQLite's
# BEGIN IMMEDIATE provided serialization locally, but the PostgreSQL compatibility
# layer translates it to BEGIN, so require a winning conditional UPDATE as well.
from .queue_claim_safety import install_queue_claim_safety as _install_queue_claim_safety
_install_queue_claim_safety()

# Worker exception strings are persisted and later exposed through /api/jobs.
# Sanitize them before jobs.py binds fail_job so credentials cannot be retained
# in operational error rows.
from .job_error_safety import install_job_error_safety as _install_job_error_safety
_install_job_error_safety()

# Execution request/result JSON is also persistent audit data. Sanitize nested
# credential-like strings before main/autopilot bind log_execution.
from .execution_log_safety import install_execution_log_safety as _install_execution_log_safety
_install_execution_log_safety()

# Successful transactional emails no longer need their raw body in the outbox.
# Install before emailer.py binds finish_email so delivered invite/reset links are
# scrubbed from future sent audit rows while failed mail remains retryable.
from .email_outbox_privacy import install_email_outbox_privacy as _install_email_outbox_privacy
_install_email_outbox_privacy()

# New workspaces should use the current Start plan and a bounded 14-day trial.
# Install this before app.main binds create_user/create_workspace. Historical
# workspace rows remain untouched and continue through the compatibility reader.
from .workspace_billing_defaults import install_workspace_billing_defaults as _install_workspace_billing_defaults
_install_workspace_billing_defaults()

# Stripe webhooks still use the full verified event in memory, but future audit
# rows only need a small non-customer summary for idempotence/troubleshooting.
# Install before any module can bind store.record_billing_event.
from .billing_event_minimization import install_billing_event_minimization as _install_billing_event_minimization
_install_billing_event_minimization()

# Harden Google read/token requests before diagnostics and connector UX wrappers
# capture the sync functions. This keeps bounded retry and payload validation at
# the base of the existing Google wrapper chain.
from .google_read_reliability import install_google_read_reliability as _install_google_read_reliability
_install_google_read_reliability()

# Harden the read-only Meta Insights path before app.main imports connector
# functions so every sync entrypoint gets the same bounded retry/pagination logic.
from .meta_read_reliability import install_meta_read_reliability as _install_meta_read_reliability
_install_meta_read_reliability()

from . import google_ads_diagnostics as _google_ads_diagnostics
from . import connector_empty_states as _connector_empty_states
from . import connector_privacy_controls as _connector_privacy_controls
from . import account_privacy_controls as _account_privacy_controls
from . import beta_readiness as _beta_readiness
from .csrf_guard import install_csrf_guard as _install_csrf_guard
from .http_error_safety import install_http_error_safety as _install_http_error_safety
from .main import app as _app
from .oauth_callback_guard import install_oauth_callback_guard as _install_oauth_callback_guard
from .production_docs_guard import install_production_docs_guard as _install_production_docs_guard
from .production_execution_guard import install_production_execution_guard as _install_production_execution_guard
from .production_token_response_guard import install_production_token_response_guard as _install_production_token_response_guard
from .public_health import install_public_health_guard as _install_public_health_guard
from .public_routing import install_public_routing as _install_public_routing
from .runtime_diagnostics import install_runtime_diagnostics as _install_runtime_diagnostics
from .security_headers import install_security_headers as _install_security_headers
from .static_entrypoint_guard import install_static_entrypoint_guard as _install_static_entrypoint_guard

_install_http_error_safety(_app)
_install_security_headers(_app)
_install_csrf_guard(_app)
_install_public_health_guard(_app)
_install_runtime_diagnostics(_app)
_install_static_entrypoint_guard(_app)
_install_production_docs_guard(_app)
_install_production_execution_guard(_app)
_install_oauth_callback_guard(_app)
_install_production_token_response_guard(_app)
_install_public_routing(_app)

__all__ = []
