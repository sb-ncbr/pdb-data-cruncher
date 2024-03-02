from src.models.transformed import DefaultPlotSettingsItem


def create_default_plot_settings(
        autoplot_data_filepath: str,
        familiar_name_translations: dict[str, str]
) -> list[DefaultPlotSettingsItem]:
    default_plot_settings = []
    # for autoplot_item in autoplot_csv_generator(autoplot_data_filepath):
    #     plot_settings_item = DefaultPlotSettingsItem()
    #     if autoplot_item.bucket_style == "step":
    #         plot_settings_item.bucked_width = autoplot_item.bucket_number
    #     else:
    #         pass  # TODO what if it isn't step? but number?
    #
    # TODO return to this later, rethink the logic

    return default_plot_settings
