
var HYDROVIEWER_PACKAGE = (function() {

    var init_map = function(){
        //create a map
        var map = new ol.Map({
            layers: [
                base_layer
            ],
            target: 'map',
            view: new ol.View({
              center: [0, 0],
              zoom: 2
            })
          });
        map_object = new Map_Object()
        map_object.add_base_layers_map(map);
        console.log(geoserver_endpoint,streams_layer_name,stations_layer_name);
        map_object.add_streams_and_stations(map,geoserver_endpoint,streams_layer_name,stations_layer_name);
        map_object.fit_view_streams_wms(map,geoserver_endpoint,geoserver_workspace,streams_layer_name);
        map_object.generate_events_map();
        // map_object.create_wms_events_popup(map,[map_object.getLayersObject().get_streams_wms()],'ecmwf-get-time-series/');
        map_object.create_wms_events_popup(map,[map_object.getLayersObject().get_streams_wms()],'ecmwf-get-time-series/','get-historic-data/','get-flow-duration-curve/','get-daily-seasonal-streamflow/','get-monthly-seasonal-streamflow/','get-forecast-percent/');
        get_warning_points_local(map);
        map_object.generate_events_map();

        // console.log(model)   
        
    }
    var get_warning_points_local = function(map){
        $.ajax({
            type: 'GET',
            url: 'get-warning-points-ecmwf/',
            dataType: 'json',

            error: function(error) {
                console.log(error);
            },
            success: function(result) {
                map_object.get_warning_points(map, result);
            }
        });
    }

    $(function() {
        $('#app-content-wrapper').removeClass('show-nav');
        $(".toggle-nav").removeClass('toggle-nav');
    
        //make sure active Plotly plots resize on window resize
        window.onresize = function() {
            $('#graph .modal-body .tab-pane.active .js-plotly-plot').each(function(){
                Plotly.Plots.resize($(this)[0]);
            });
        };
    
        init_map();
    
    })


})()



function map_events(wms_layers) {
    map.on('pointermove', function(evt) {
        if (evt.dragging) {
            return;
        }
        var model = $('#model option:selected').text();
        var pixel = map.getEventPixel(evt.originalEvent);
        var hit = map.forEachLayerAtPixel(pixel, function(layer) {
            if ( wms_layers.filter((wms_layer)=> layer== wms_layer )) {
            //if(layer == feature_layer || layer == feature_layer2) {    
                current_layer = layer;
                return true;
            }

            map.getTargetElement().style.cursor = hit ? 'pointer' : '';
        });
    })

    map.on("singleclick", function(evt) {
        var model = $('#model option:selected').text();

        if (map.getTargetElement().style.cursor == "pointer") {

            var view = map.getView();
            var viewResolution = view.getResolution();

            var wms_url = current_layer.getSource().getGetFeatureInfoUrl(evt.coordinate, viewResolution, view.getProjection(), { 'INFO_FORMAT': 'application/json' }); //Get the wms url for the clicked point
            
            $("#graph").modal('show');
            $("#tbody").empty()
            $('#long-term-chart').addClass('d-none');
            $('#historical-chart').addClass('d-none');
            $('#fdc-chart').addClass('d-none');
            $('#seasonal_d-chart').addClass('d-none');
            $('#seasonal_m-chart').addClass('d-none');
            $('#download_forecast').addClass('d-none');
            $('#download_era_5').addClass('d-none');

            $loading.removeClass('d-none');
            //Retrieving the details for clicked point via the url
            $('#dates').addClass('d-none');
            //$('#plot').addClass('d-none');
            $.ajax({
                type: "GET",
                url: wms_url,
                dataType: 'json',
                success: function(result) {
                    var model = $('#model option:selected').text();
                    comid = result["features"][0]["properties"]["COMID"];

                    var startdate = '';
                    if ("derived_fr" in (result["features"][0]["properties"])) {
                        var watershed = (result["features"][0]["properties"]["derived_fr"]).toLowerCase().split('-')[0];
                        var subbasin = (result["features"][0]["properties"]["derived_fr"]).toLowerCase().split('-')[1];
                    } else if (geoserver_region) {
                        var watershed = geoserver_region.split('-')[0]
                        var subbasin = geoserver_region.split('-')[1];
                    } else {
                        var watershed = (result["features"][0]["properties"]["watershed"]).toLowerCase();
                        var subbasin = (result["features"][0]["properties"]["subbasin"]).toLowerCase();
                    }

                    get_available_dates(model, watershed, subbasin, comid);
                    get_time_series(model, watershed, subbasin, comid, startdate);
                    get_historic_data(model, watershed, subbasin, comid, startdate);
                    get_flow_duration_curve(model, watershed, subbasin, comid, startdate);
                    get_daily_seasonal_streamflow(model, watershed, subbasin, comid, startdate);
                    get_monthly_seasonal_streamflow(model, watershed, subbasin, comid, startdate);
                    if (model === 'ECMWF-RAPID') {
                        get_forecast_percent(watershed, subbasin, comid, startdate);
                    };

                    var workspace = geoserver_workspace;

                    $('#info').addClass('d-none');
                    add_feature(model, workspace, comid);

                },
                error: function(XMLHttpRequest, textStatus, errorThrown) {
                    console.log(Error);
                }
            });           
        };
    });

}

function add_feature(model, workspace, comid) {
    map.removeLayer(featureOverlay);

    var watershed = $('#watershedSelect option:selected').text().split(' (')[0].replace(' ', '_').toLowerCase();
    var subbasin = $('#watershedSelect option:selected').text().split(' (')[1].replace(')', '').toLowerCase();

    if (model === 'ECMWF-RAPID') {
        var vectorSource = new ol.source.Vector({
            format: new ol.format.GeoJSON(),
            url: function(extent) {
                return geoserver_endpoint.replace(/\/$/, "") + '/' + 'ows?service=wfs&' +
                    'version=2.0.0&request=getfeature&typename=' + workspace + ':' + watershed + '-' + subbasin + '-drainage_line' + '&CQL_FILTER=COMID=' + comid + '&outputFormat=application/json&srsname=EPSG:3857&' + ',EPSG:3857';
            },
            strategy: ol.loadingstrategy.bbox
        });

        featureOverlay = new ol.layer.Vector({
            source: vectorSource,
            style: new ol.style.Style({
                stroke: new ol.style.Stroke({
                    color: '#00BFFF',
                    width: 8
                })
            })
        });
        map.addLayer(featureOverlay);
        map.getLayers().item(5);

    } else if (model === 'LIS-RAPID') {
        var vectorSource;
        $.ajax({
            type: 'GET',
            url: 'get-lis-shp/',
            dataType: 'json',
            data: {
                'model': model,
                'watershed': workspace[0],
                'subbasin': workspace[1]
            },
            success: function(result) {
                JSON.parse(result.options).features.forEach(function(elm) {
                    if (elm.properties.COMID === parseInt(comid)) {
                        var filtered_json = {
                            "type": "FeatureCollection",
                            "features": [elm]
                        };
                        vectorSource = new ol.source.Vector({
                            features: (new ol.format.GeoJSON()).readFeatures(filtered_json)
                        });
                    }
                });

                featureOverlay = new ol.layer.Vector({
                    source: vectorSource,
                    style: new ol.style.Style({
                        stroke: new ol.style.Stroke({
                            color: '#00BFFF',
                            width: 8
                        })
                    })
                });
                map.addLayer(featureOverlay);
                map.getLayers().item(5);
            }
        });

    } else if (model === 'HIWAT-RAPID') {
        var vectorSource;
        $.ajax({
            type: 'GET',
            url: 'get-hiwat-shp/',
            dataType: 'json',
            data: {
                'model': model,
                'watershed': workspace[0],
                'subbasin': workspace[1]
            },
            success: function(result) {
                JSON.parse(result.options).features.forEach(function(elm) {
                    if (elm.properties.COMID === parseInt(comid)) {
                        var filtered_json = {
                            "type": "FeatureCollection",
                            "features": [elm]
                        };
                        vectorSource = new ol.source.Vector({
                            features: (new ol.format.GeoJSON()).readFeatures(filtered_json)
                        });
                    }
                });

                featureOverlay = new ol.layer.Vector({
                    source: vectorSource,
                    style: new ol.style.Style({
                        stroke: new ol.style.Stroke({
                            color: '#00BFFF',
                            width: 8
                        })
                    })
                });
                map.addLayer(featureOverlay);
                map.getLayers().item(5);
            }
        });
    }
}








$(function() {

});
