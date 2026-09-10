from .production_env_guards import apply_production_env_guards as _apply_production_env_guards

# Production safety overrides must run before app.main is imported because
# some beta-only behavior is selected from environment flags at import time.
_apply_production_env_guards()

# Install KPI semantic translation before app.main/core/brief modules import
# store helpers. This keeps historical GA sessions out of paid-click metrics
# without a risky production data migration.
from .kpi_semantics import install_kpi_semantics_guard as _install_kpi_semantics_guard
_install_kpi_semantics_guard()

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
from .public_health import install_public_health_guard as _install_public_health_guard
from .public_routing import install_public_routing as _install_public_routing
from .runtime_diagnostics import install_runtime_diagnostics as _install_runtime_diagnostics

_install_http_error_safety(_app)
_install_csrf_guard(_app)
_install_public_health_guard(_app)
_install_runtime_diagnostics(_app)
_install_public_routing(_app)

__all__ = []
