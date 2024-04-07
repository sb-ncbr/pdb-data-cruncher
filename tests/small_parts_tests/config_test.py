import pytest

from src.config import Config, DefaultPlotSettingsConfig, FactorHierarchyConfig


def test_multiple_run_only_options_are_not_allowed():
    config = Config()
    config.run_data_download_only = True
    config.validate()  # only one "only" option is valid

    config.run_data_extraction_only = True
    with pytest.raises(ValueError):
        config.validate()


def test_default_config_is_valid():
    config = Config()
    config.validate()  # default setting does not raise


# bucket sizes get validated
@pytest.mark.parametrize("invalid_bucket_sizes", [[], [1, 10], [10, 20, 100], [10, 20, 15]])
def test_bucket_base_sizes_get_validated(invalid_bucket_sizes):
    default_plot_settings_config = DefaultPlotSettingsConfig(allowed_bucket_base_sizes=invalid_bucket_sizes)
    factor_hierarchy_config = FactorHierarchyConfig(allowed_slider_base_sizes=invalid_bucket_sizes)

    with pytest.raises(ValueError):
        default_plot_settings_config.validate()

    with pytest.raises(ValueError):
        factor_hierarchy_config.validate()


def test_current_date_string_gets_validated():
    config = Config()
    config.current_formatted_date = ""
    with pytest.raises(ValueError):
        config.validate()
    config.current_formatted_date = "2020-01-01"
    with pytest.raises(ValueError):
        config.validate()
    config.current_formatted_date = "20200101010101"
    with pytest.raises(ValueError):
        config.validate()
    config.current_formatted_date = "20240101"
    config.validate()
