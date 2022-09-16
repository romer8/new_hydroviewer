from tethys_sdk.base import TethysAppBase, url_map_maker
from tethys_sdk.app_settings import CustomSetting, SpatialDatasetServiceSetting


class NewHydroviewer(TethysAppBase):
    """
    Tethys app class for New Hydroviewer.
    """

    name = 'New Hydroviewer'
    index = 'new_hydroviewer:home'
    icon = 'new_hydroviewer/images/icon.gif'
    package = 'new_hydroviewer'
    root_url = 'new-hydroviewer'
    color = '#c0392b'
    description = ''
    tags = ''
    enable_feedback = False
    feedback_emails = []

    def url_maps(self):
        """
        Add controllers
        """
        UrlMap = url_map_maker(self.root_url)

        url_maps = (
            UrlMap(
                name='home',
                url='new-hydroviewer',
                controller='new_hydroviewer.controllers.home'
            ),
            UrlMap(
                name='home',
                url='get-warning-points-ecmwf/',
                controller='new_hydroviewer.controllers.get_warning_points'
            ),
        )

        return url_maps


    def spatial_dataset_service_settings(self):
        """
        Spatial_dataset_service_settings method.
        """
        return (
            SpatialDatasetServiceSetting(
                name='main_geoserver',
                description='spatial dataset service for app to use (https://tethys2.byu.edu/geoserver/rest/)',
                engine=SpatialDatasetServiceSetting.GEOSERVER,
                required=True,
            ),
        )

    def custom_settings(self):
        return (
            CustomSetting(
                name='api_source',
                type=CustomSetting.TYPE_STRING,
                description='Web site where the GESS REST API is available',
                required=True,
                default='https://geoglows.ecmwf.int',
            ),
            CustomSetting(
                name='workspace',
                type=CustomSetting.TYPE_STRING,
                description='Workspace within Geoserver where web service is',
                required=True,
                default='peru_hydroviewer',
            ),
            CustomSetting(
                name='region',
                type=CustomSetting.TYPE_STRING,
                description='GESS Region',
                required=True,
                default='south_america-geoglows',
            ),
            CustomSetting(
                name='keywords',
                type=CustomSetting.TYPE_STRING,
                description='Keyword(s) for visualizing watersheds in HydroViewer',
                required=True,
                default='peru, south_america',
            ),
            CustomSetting(
                name='zoom_info',
                type=CustomSetting.TYPE_STRING,
                description='lon,lat,zoom_level',
                required=True,
                default='-76,-10,5',
            ),
            CustomSetting(
                name='default_model_type',
                type=CustomSetting.TYPE_STRING,
                description='Default Model Type : (Options : ECMWF-RAPID, LIS-RAPID)',
                required=False,
                default='ECMWF-RAPID',
            ),
            CustomSetting(
                name='static_GeoJSON_path',
                type=CustomSetting.TYPE_STRING,
                description='Default GeoJson path for the different regions',
                required=False,
            ),
            CustomSetting(
                name='reach_ids_path',
                type=CustomSetting.TYPE_STRING,
                description='Default path for the different reach ids',
                required=False,
            ),
            CustomSetting(
                name='Stations_Layer_Name',
                type=CustomSetting.TYPE_STRING,
                description='Name of the Stations Layer in the GeoServer Service',
                required=False,
            ),
            CustomSetting(
                name='Streams_Layer_Name',
                type=CustomSetting.TYPE_STRING,
                description='Name of the Streams Layer in the GeoServer Service',
                required=False,
            ),
            CustomSetting(
                name='Level_boundaries',
                type=CustomSetting.TYPE_STRING,
                description='Name of the Level Boundaries in the GeoServer Service',
                required=False,
            ),
            CustomSetting(
                name='default_watershed_name',
                type=CustomSetting.TYPE_STRING,
                description='Default Watershed Name: (For ex: "South America (Brazil)") ',
                required=False,
                default='South America (Brazil)',
            ),
            CustomSetting(
                name='show_dropdown',
                type=CustomSetting.TYPE_BOOLEAN,
                description='Hide Watershed Options when default present (True or False) ',
                required=True,
                value=True
            ),
            CustomSetting(
                name='lis_path',
                type=CustomSetting.TYPE_STRING,
                description='Path to local LIS-RAPID directory',
                required=False
            ),
            CustomSetting(
                name='hiwat_path',
                type=CustomSetting.TYPE_STRING,
                description='Path to local HIWAT-RAPID directory',
                required=False
            ),
        )
