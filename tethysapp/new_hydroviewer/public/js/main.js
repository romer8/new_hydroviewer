
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
        map_object = new Map()
        map_object.add_base_layers_map(map);
        console.log(geoserver_endpoint,streams_layer_name,stations_layer_name);
        map_object.add_streams_and_stations(map,geoserver_endpoint,streams_layer_name,stations_layer_name);
        map_object.fit_view_streams_wms(map,geoserver_endpoint,geoserver_workspace,streams_layer_name);
        map_object.generate_events_map();

        get_warning_points_local(map);
        console.log(model)   
        
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






$(function() {
    // $('#app-content-wrapper').removeClass('show-nav');
    // $(".toggle-nav").removeClass('toggle-nav');

    // //make sure active Plotly plots resize on window resize
    // window.onresize = function() {
    //     $('#graph .modal-body .tab-pane.active .js-plotly-plot').each(function(){
    //         Plotly.Plots.resize($(this)[0]);
    //     });
    // };

    // init_map();


    // map_events();
    // submit_model();
    // resize_graphs();
    // // If there is a defined Watershed, then lets render it and hide the controls
    // let ws_val = $('#watershed').find(":selected").text();
    // if (ws_val && ws_val !== 'Select Watershed') {
    //     console.log("hola")
    //     view_watershed();
    //     $("[name='update_button']").hide();
    // }
    // else{
    //     console.log("Iam here")
    //     view_watershed();

    // }

    // // If there is a button to save default WS, let's add handler
    // $("[name='update_button']").click(() => {
    //     $.ajax({
    //         url: 'admin/setdefault',
    //         type: 'GET',
    //         dataType: 'json',
    //         data: {
    //             'ws_name': $('#model').find(":selected").text(),
    //             'model_name': $('#watershed').find(":selected").text()
    //         },
    //         success: function() {
    //             // Remove the set default button
    //             $("[name='update_button']").hide(500);
    //             console.log('Updated Defaults Successfully');
    //         }
    //     });
    // })


    // $('#datesSelect').change(function() { //when date is changed
    // 	//console.log($("#datesSelect").val());

    //     //var sel_val = ($('#datesSelect option:selected').val()).split(',');
    //     sel_val = $("#datesSelect").val()

    //     //var startdate = sel_val[0];
    //     var startdate = sel_val;
    //     startdate = startdate.replace("-","");
    //     startdate = startdate.replace("-","");

    //     //var watershed = sel_val[1];
    //     var watershed = 'south_america';

    //     //var subbasin = sel_val[2];
    //     var subbasin = 'geoglows';

    //     //var comid = sel_val[3];
    //     var model = 'ECMWF-RAPID';

    //     $loading.removeClass('hidden');
    //     get_time_series(model, watershed, subbasin, comid, startdate);
    //     get_forecast_percent(watershed, subbasin, comid, startdate);
    // });
});



// // Regions gizmo listener
// $('#regions').change(function() {getRegionGeoJsons()});