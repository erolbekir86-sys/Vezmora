from .production_env_guards import apply_production_env_guards as _apply_production_env_guards

# Production safety overrides must run before app.main is imported because
# some beta-only behavior is selected from environment flags at import time.
_apply_production_env_guards()

from . import google_ads_diagnostics as _google_ads_diagnostics
from . import connector_empty_states as _connector_empty_states
from . import connector_privacy_controls as _connector_privacy_controls
from . import account_privacy_controls as _account_privacy_controls
from . import beta_readiness as _beta_readiness
from .csrf_guard import install_csrf_guard as _install_csrf_guard
from .http_error_safety import install_http_error_safety as _install_http_error_safety
from .main import app as _app
from .public_routing import install_public_routing as _install_public_routing
from .runtime_diagnostics import install_runtime_diagnostics as _install_runtime_diagnostics

_install_http_error_safety(_app)
_install_csrf_guard(_app)
_install_runtime_diagnostics(_app)
_install_public_routing(_app)

__all__ = []
