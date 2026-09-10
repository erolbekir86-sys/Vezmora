from __future__ import annotations

from app.models import ConnectorSettings


def test_connector_settings_trim_copy_pasted_identifiers() -> None:
    settings = ConnectorSettings(
        analytics_property_id="  123456789  ",
        ads_customer_id="  123-456-7890  ",
        meta_ad_account_id="  act_123456  ",
    )

    assert settings.analytics_property_id == "123456789"
    assert settings.ads_customer_id == "123-456-7890"
    assert settings.meta_ad_account_id == "act_123456"


def test_connector_settings_map_blank_identifiers_to_unset() -> None:
    settings = ConnectorSettings(
        analytics_property_id="   ",
        ads_customer_id="\t",
        meta_ad_account_id="\n",
    )

    assert settings.analytics_property_id is None
    assert settings.ads_customer_id is None
    assert settings.meta_ad_account_id is None


def test_connector_settings_preserve_none() -> None:
    settings = ConnectorSettings()
    assert settings.analytics_property_id is None
    assert settings.ads_customer_id is None
    assert settings.meta_ad_account_id is None
