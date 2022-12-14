from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from tethys_sdk.gizmos import *
from django.http import HttpResponse, JsonResponse
from tethys_sdk.permissions import has_permission
from tethys_sdk.base import TethysAppBase
from tethys_sdk.gizmos import PlotlyView
from tethys_sdk.workspaces import app_workspace
from tethys_sdk.gizmos import Button, DatePicker, PlotlyView, SelectInput
import asyncio

import os
import pytz
import requests
from requests.auth import HTTPBasicAuth
import json
import urllib.request
import urllib.error
import urllib.parse
import numpy as np
import netCDF4 as nc
import pandas as pd
import io
import geoglows
import hydrostats

from osgeo import ogr
from osgeo import osr
from csv import writer as csv_writer
import csv
import scipy.stats as sp
import datetime as dt
import ast
import plotly.graph_objs as go

from dateutil.relativedelta import relativedelta
from bs4 import BeautifulSoup
from .app import NewHydroviewer as app
from .helpers import *
from tethysext.hydroviewer.controllers.ecmwf import Ecmf
base_name = __package__.split('.')[-1]

ecmf_object =  Ecmf()

def set_custom_setting(defaultModelName, defaultWSName):

    from tethys_apps.models import TethysApp
    db_app = TethysApp.objects.get(package=app.package)
    custom_settings = db_app.custom_settings

    db_setting = db_app.custom_settings.get(name='default_model_type')
    db_setting.value = defaultModelName
    db_setting.save()

    db_setting = db_app.custom_settings.get(name='default_watershed_name')
    db_setting.value = defaultWSName
    db_setting.save()


def home(request):

    # Check if we have a default model. If we do, then redirect the user to the default model's page
    default_model = app.get_custom_setting('default_model_type')
    if default_model:
        model_func = switch_model(default_model)
        if model_func is not 'invalid':
            return globals()[model_func](request)
        else:
            return home_standard(request)
    else:
        return home_standard(request)


def home_standard(request):
    model_input = SelectInput(display_text='',
                              name='model',
                              multiple=False,
                              options=[('Select Model', ''), ('ECMWF-RAPID', 'ecmwf'), ('LIS-RAPID', 'lis')],
                              initial=['Select Model'],
                              original=True)

    zoom_info = TextInput(display_text='',
                          initial=json.dumps(app.get_custom_setting('zoom_info')),
                          name='zoom_info',
                          disabled=True)

    context = {
        "base_name": base_name,
        "model_input": model_input,
        "zoom_info": zoom_info
    }

    return render(request, '{0}/home.html'.format(base_name), context)

def ecmwf(request):
    # ecmf_object =  Ecmf()
    basic_settings = ecmf_object.get_start_custom_settings(request)
    dates_watershed = ecmf_object.get_available_dates_watershed(request)
    # Date Picker Options
    date_picker = DatePicker(name='datesSelect',
                                display_text='Date',
                                autoclose=True,
                                format='yyyy-mm-dd',
                                start_date=dates_watershed[-1][0],
                                end_date=dates_watershed[1][0],
                                start_view='month',
                                today_button=True,
                                initial='')
    today = dt.datetime.now()
    date = str(today.strftime("%d")) + '/' + str(today.strftime("%m")) + '/' + str(today.year)
    date2 = str(today.strftime("%d")) + '/' + str(today.strftime("%m")) + '/' + str(int(str(today.year)) - 1)

    startdateobs = DatePicker(name='startdateobs',
                            display_text='Start Date',
                            autoclose=True,
                            format='dd/mm/yyyy',
                            start_date='01/01/1950',
                            start_view='month',
                            today_button=True,
                            initial=date2,
                            classes='datepicker')

    enddateobs = DatePicker(name='enddateobs',
                            display_text='End Date',
                            autoclose=True,
                            format='dd/mm/yyyy',
                            start_date='01/01/1950',
                            start_view='month',
                            today_button=True,
                            initial=date,
                            classes='datepicker')

    dates_context = {
        "startdateobs": startdateobs,
        "enddateobs": enddateobs,
        "date_picker": date_picker,
    }

    basic_settings.update(dates_context)

    context = basic_settings
    #adding default model type if needed 
    context.update({
        "model":app.get_custom_setting("default_model_type")
    })
    return render(request, 'new_hydroviewer/home.html', context)
    # return render(request, 'hydroviewer/ecmwf.html', context)


def get_warning_points(request):
    # ecmf_object =  Ecmf()
    warning_points = ecmf_object.get_warning_points(request)
    return JsonResponse(warning_points)


def ecmwf_get_time_series(request):
    hydroviewer_figure = ecmf_object.ecmwf_get_time_series(request);
    chart_obj = PlotlyView(hydroviewer_figure)

    context = {
        'gizmo_object': chart_obj,
    }
    return render(request, f'{base_name}/gizmo_ajax.html', context)
def get_historic_data(request):
    hydroviewer_figure = ecmf_object.get_historic_data(request);
    chart_obj = PlotlyView(hydroviewer_figure)

    context = {
        'gizmo_object': chart_obj,
    }
    return render(request, f'{base_name}/gizmo_ajax.html', context)

# def get_charts(request):
    
#     asyncio.run(ecmf_object.async_request(request))
#     pass

# async def async_request(self,request):
#     async_client = httpx.AsyncClient()

#     tasks = [asyncio.create_task(self.forecast_async_wrapper(request,async_client))]
#     # tasks = [asyncio.create_task(self.forecast_async_wrapper(request,async_client)),asyncio.create_task(self.historical_async_wrapper(request,async_client))]

#     results = asyncio.gather(*tasks)
# def ecmwf(request):

#     # Can Set Default permissions : Only allowed for admin users
#     can_update_default = has_permission(request, 'update_default')

#     if(can_update_default):
#         defaultUpdateButton = Button(
#             display_text='Save',
#             name='update_button',
#             style='success',
#             attributes={
#                 'data-toggle': 'tooltip',
#                 'data-placement': 'bottom',
#                 'title': 'Save as Default Options for WS'
#             })
#     else:
#         defaultUpdateButton = False

#     # Check if we need to hide the WS options dropdown.
#     hiddenAttr = ""
#     if app.get_custom_setting('show_dropdown') and app.get_custom_setting('default_model_type') and app.get_custom_setting('default_watershed_name'):
#         hiddenAttr = "hidden"

#     init_model_val = request.GET.get('model', False) or app.get_custom_setting('default_model_type') or 'Select Model'
#     init_ws_val = app.get_custom_setting('default_watershed_name') or 'Select Watershed'

#     model_input = SelectInput(display_text='',
#                               name='model',
#                               multiple=False,
#                               options=[('Select Model', ''), ('ECMWF-RAPID', 'ecmwf'),
#                                        ('LIS-RAPID', 'lis'), ('HIWAT-RAPID', 'hiwat')],
#                               initial=[init_model_val],
#                               classes=hiddenAttr,
#                               original=True)

#     # uncomment for displaying watersheds in the SPT
#     # res = requests.get(app.get_custom_setting('api_source') + '/apps/streamflow-prediction-tool/api/GetWatersheds/',
#     #                    headers={'Authorization': 'Token ' + app.get_custom_setting('spt_token')})
#     #
#     # watershed_list_raw = json.loads(res.content)
#     #
#     # app.get_custom_setting('keywords').lower().replace(' ', '').split(',')
#     # watershed_list = [value for value in watershed_list_raw if
#     #                   any(val in value[0].lower().replace(' ', '') for
#     #                       val in app.get_custom_setting('keywords').lower().replace(' ', '').split(','))]

#     # Retrieve a geoserver engine and geoserver credentials.
#     geoserver_engine = app.get_spatial_dataset_service(
#         name='main_geoserver', as_engine=True)

#     geos_username = geoserver_engine.username
#     geos_password = geoserver_engine.password
#     my_geoserver = geoserver_engine.endpoint.replace('rest', '')

#     watershed_list = [['Select Watershed', '']]  # + watershed_list

#     res2 = requests.get(my_geoserver + '/rest/workspaces/' + app.get_custom_setting('workspace') +
#                         '/featuretypes.json', auth=HTTPBasicAuth(geos_username, geos_password), verify=False)

#     for i in range(len(json.loads(res2.content)['featureTypes']['featureType'])):
#         raw_feature = json.loads(res2.content)['featureTypes']['featureType'][i]['name']
#         if 'drainage_line' in raw_feature and any(n in raw_feature for n in app.get_custom_setting('keywords').replace(' ', '').split(',')):
#             feat_name = raw_feature.split('-')[0].replace('_', ' ').title() + ' (' + \
#                 raw_feature.split('-')[1].replace('_', ' ').title() + ')'
#             if feat_name not in str(watershed_list):
#                 watershed_list.append([feat_name, feat_name])

#     # Add the default WS if present and not already in the list
#     if init_ws_val and init_ws_val not in str(watershed_list):
#         watershed_list.append([init_ws_val, init_ws_val])

#     watershed_select = SelectInput(display_text='',
#                                    name='watershed',
#                                    options=watershed_list,
#                                    initial=[init_ws_val],
#                                    original=True,
#                                    classes=hiddenAttr,
#                                    attributes={'onchange': "javascript:view_watershed();"+hiddenAttr}
#                                    )

#     zoom_info = TextInput(display_text='',
#                           initial=json.dumps(app.get_custom_setting('zoom_info')),
#                           name='zoom_info',
#                           disabled=True)

#     # Retrieve a geoserver engine and geoserver credentials.
#     geoserver_engine = app.get_spatial_dataset_service(
#         name='main_geoserver', as_engine=True)

#     my_geoserver = geoserver_engine.endpoint.replace('rest', '')

#     geoserver_base_url = my_geoserver
#     geoserver_workspace = app.get_custom_setting('workspace')
#     region = app.get_custom_setting('region')
#     geoserver_endpoint = TextInput(display_text='',
#                                    initial=json.dumps([geoserver_base_url, geoserver_workspace, region]),
#                                    name='geoserver_endpoint',
#                                    disabled=True)

#     today = dt.datetime.now()
#     year = str(today.year)
#     month = str(today.strftime("%m"))
#     day = str(today.strftime("%d"))
#     date = day + '/' + month + '/' + year
#     lastyear = int(year) - 1
#     date2 = day + '/' + month + '/' + str(lastyear)

#     startdateobs = DatePicker(name='startdateobs',
#                               display_text='Start Date',
#                               autoclose=True,
#                               format='dd/mm/yyyy',
#                               start_date='01/01/1950',
#                               start_view='month',
#                               today_button=True,
#                               initial=date2,
#                               classes='datepicker')

#     enddateobs = DatePicker(name='enddateobs',
#                             display_text='End Date',
#                             autoclose=True,
#                             format='dd/mm/yyyy',
#                             start_date='01/01/1950',
#                             start_view='month',
#                             today_button=True,
#                             initial=date,
#                             classes='datepicker')

#     res = requests.get('https://geoglows.ecmwf.int/api/AvailableDates/?region=central_america-geoglows', verify=False)
#     data = res.json()
#     dates_array = (data.get('available_dates'))

#     dates = []

#     for date in dates_array:
#         if len(date) == 10:
#             date_mod = date + '000'
#             date_f = dt.datetime.strptime(date_mod, '%Y%m%d.%H%M').strftime('%Y-%m-%d %H:%M')
#         else:
#             date_f = dt.datetime.strptime(date, '%Y%m%d.%H%M').strftime('%Y-%m-%d')
#             date = date[:-3]
#         dates.append([date_f, date])
#         dates = sorted(dates)

#     dates.append(['Select Date', dates[-1][1]])
#     # print(dates)
#     dates.reverse()

#     # Date Picker Options
#     date_picker = DatePicker(name='datesSelect',
#                              display_text='Date',
#                              autoclose=True,
#                              format='yyyy-mm-dd',
#                              start_date=dates[-1][0],
#                              end_date=dates[1][0],
#                              start_view='month',
#                              today_button=True,
#                              initial='')

#     region_index = json.load(open(os.path.join(os.path.dirname(__file__), 'public', 'geojson', 'index.json')))
#     regions = SelectInput(
#         display_text='Zoom to a Region:',
#         name='regions',
#         multiple=False,
#         original=True,
#         options=[(region_index[opt]['name'], opt) for opt in region_index]
#     )

#     context = {
#         "base_name": base_name,
#         "model_input": model_input,
#         "watershed_select": watershed_select,
#         "zoom_info": zoom_info,
#         "geoserver_endpoint": geoserver_endpoint,
#         "defaultUpdateButton": defaultUpdateButton,
#         "startdateobs": startdateobs,
#         "enddateobs": enddateobs,
#         "date_picker": date_picker,
#         "regions": regions
#     }

#     return render(request, '{0}/ecmwf.html'.format(base_name), context)


# def lis(request):

#     default_model = app.get_custom_setting('default_model_type')
#     init_model_val = request.GET.get('model', False) or default_model or 'Select Model'
#     init_ws_val = app.get_custom_setting('default_watershed_name') or 'Select Watershed'

#     model_input = SelectInput(display_text='',
#                               name='model',
#                               multiple=False,
#                               options=[('Select Model', ''), ('ECMWF-RAPID', 'ecmwf'),
#                                        ('LIS-RAPID', 'lis'), ('HIWAT-RAPID', 'hiwat')],
#                               initial=[init_model_val],
#                               original=True)

#     watershed_list = [['Select Watershed', '']]

#     if app.get_custom_setting('lis_path'):
#         res = os.listdir(app.get_custom_setting('lis_path'))

#         for i in res:
#             feat_name = i.split('-')[0].replace('_', ' ').title() + ' (' + \
#                 i.split('-')[1].replace('_', ' ').title() + ')'
#             if feat_name not in str(watershed_list):
#                 watershed_list.append([feat_name, i])

#     # Add the default WS if present and not already in the list
#     # Not sure if this will work with LIS type. Need to test it out.
#     if default_model == 'LIS-RAPID' and init_ws_val and init_ws_val not in str(watershed_list):
#         watershed_list.append([init_ws_val, init_ws_val])

#     watershed_select = SelectInput(display_text='',
#                                    name='watershed',
#                                    options=watershed_list,
#                                    initial=[init_ws_val],
#                                    original=True,
#                                    attributes={'onchange': "javascript:view_watershed();"}
#                                    )

#     zoom_info = TextInput(display_text='',
#                           initial=json.dumps(app.get_custom_setting('zoom_info')),
#                           name='zoom_info',
#                           disabled=True)
#     context = {
#         "base_name": base_name,
#         "model_input": model_input,
#         "watershed_select": watershed_select,
#         "zoom_info": zoom_info
#     }

#     return render(request, '{0}/lis.html'.format(base_name), context)


# def hiwat(request):
#     default_model = app.get_custom_setting('default_model_type')
#     init_model_val = request.GET.get('model', False) or default_model or 'Select Model'
#     init_ws_val = app.get_custom_setting('default_watershed_name') or 'Select Watershed'

#     model_input = SelectInput(display_text='',
#                               name='model',
#                               multiple=False,
#                               options=[('Select Model', ''), ('ECMWF-RAPID', 'ecmwf'),
#                                        ('LIS-RAPID', 'lis'), ('HIWAT-RAPID', 'hiwat')],
#                               initial=[init_model_val],
#                               original=True)

#     watershed_list = [['Select Watershed', '']]

#     if app.get_custom_setting('lis_path'):
#         res = os.listdir(app.get_custom_setting('hiwat_path'))

#         for i in res:
#             feat_name = i.split('-')[0].replace('_', ' ').title() + ' (' + \
#                 i.split('-')[1].replace('_', ' ').title() + ')'
#             if feat_name not in str(watershed_list):
#                 watershed_list.append([feat_name, i])

#     # Add the default WS if present and not already in the list
#     # Not sure if this will work with LIS type. Need to test it out.
#     if default_model == 'HIWAT-RAPID' and init_ws_val and init_ws_val not in str(watershed_list):
#         watershed_list.append([init_ws_val, init_ws_val])

#     watershed_select = SelectInput(display_text='',
#                                    name='watershed',
#                                    options=watershed_list,
#                                    initial=[init_ws_val],
#                                    original=True,
#                                    attributes={'onchange': "javascript:view_watershed();"}
#                                    )

#     zoom_info = TextInput(display_text='',
#                           initial=json.dumps(app.get_custom_setting('zoom_info')),
#                           name='zoom_info',
#                           disabled=True)
#     context = {
#         "base_name": base_name,
#         "model_input": model_input,
#         "watershed_select": watershed_select,
#         "zoom_info": zoom_info
#     }

#     return render(request, '{0}/hiwat.html'.format(base_name), context)

# @app_workspace
# def get_warning_points(request,app_workspace):
#     get_data = request.GET
#     peru_id_path = os.path.join(app_workspace.path, 'peru_reachids.csv')
#     reach_pds = pd.read_csv(peru_id_path)
#     reach_ids_list = reach_pds['COMID'].tolist()
#     return_obj = {}
#     # print("REACH_PDS")
#     # print(reach_ids_list)
#     if get_data['model'] == 'ECMWF-RAPID':
#         try:
#             watershed = get_data['watershed']
#             subbasin = get_data['subbasin']

#             res = requests.get(app.get_custom_setting('api_source') + '/api/ForecastWarnings/?region=' + watershed + '-' + 'geoglows' + '&return_format=csv', verify=False).content

#             res_df = pd.read_csv(io.StringIO(res.decode('utf-8')), index_col=0)
#             cols = ['date_exceeds_return_period_2', 'date_exceeds_return_period_5', 'date_exceeds_return_period_10', 'date_exceeds_return_period_25', 'date_exceeds_return_period_50', 'date_exceeds_return_period_100']

#             res_df["rp_all"] = res_df[cols].apply(lambda x: ','.join(x.replace(np.nan, '0')), axis=1)

#             test_list = res_df["rp_all"].tolist()

#             final_new_rp = []
#             for term in test_list:
#                 new_rp = []
#                 terms = term.split(',')
#                 for te in terms:
#                     if te is not '0':
#                         # print('yeah')
#                         new_rp.append(1)
#                     else:
#                         new_rp.append(0)
#                 final_new_rp.append(new_rp)

#             res_df['rp_all2'] = final_new_rp

#             res_df = res_df.reset_index()
#             res_df = res_df[res_df['comid'].isin(reach_ids_list)]

#             d = {'comid': res_df['comid'].tolist(), 'stream_order': res_df['stream_order'].tolist(), 'lat': res_df['stream_lat'].tolist(), 'lon': res_df['stream_lon'].tolist()}
#             df_final = pd.DataFrame(data=d)

#             df_final[['rp_2', 'rp_5', 'rp_10', 'rp_25', 'rp_50', 'rp_100']] = pd.DataFrame(res_df.rp_all2.tolist(), index=df_final.index)
#             d2 = {'comid': res_df['comid'].tolist(), 'stream_order': res_df['stream_order'].tolist(), 'lat': res_df['stream_lat'].tolist(), 'lon': res_df['stream_lon'].tolist(), 'rp': df_final['rp_2']}
#             d5 = {'comid': res_df['comid'].tolist(), 'stream_order': res_df['stream_order'].tolist(), 'lat': res_df['stream_lat'].tolist(), 'lon': res_df['stream_lon'].tolist(), 'rp': df_final['rp_5']}
#             d10 = {'comid': res_df['comid'].tolist(), 'stream_order': res_df['stream_order'].tolist(), 'lat': res_df['stream_lat'].tolist(), 'lon': res_df['stream_lon'].tolist(), 'rp': df_final['rp_10']}
#             d25 = {'comid': res_df['comid'].tolist(), 'stream_order': res_df['stream_order'].tolist(), 'lat': res_df['stream_lat'].tolist(), 'lon': res_df['stream_lon'].tolist(), 'rp': df_final['rp_25']}
#             d50 = {'comid': res_df['comid'].tolist(), 'stream_order': res_df['stream_order'].tolist(), 'lat': res_df['stream_lat'].tolist(), 'lon': res_df['stream_lon'].tolist(), 'rp': df_final['rp_50']}
#             d100 = {'comid': res_df['comid'].tolist(), 'stream_order': res_df['stream_order'].tolist(), 'lat': res_df['stream_lat'].tolist(), 'lon': res_df['stream_lon'].tolist(), 'rp': df_final['rp_100']}

#             df_final_2 = pd.DataFrame(data=d2)
#             df_final_2 = df_final_2[df_final_2['rp'] > 0]
#             df_final_5 = pd.DataFrame(data=d5)
#             df_final_5 = df_final_5[df_final_5['rp'] > 0]
#             df_final_10 = pd.DataFrame(data=d10)
#             df_final_10 = df_final_10[df_final_10['rp'] > 0]
#             df_final_25 = pd.DataFrame(data=d25)
#             df_final_25 = df_final_25[df_final_25['rp'] > 0]
#             df_final_50 = pd.DataFrame(data=d50)
#             df_final_50 = df_final_50[df_final_50['rp'] > 0]
#             df_final_100 = pd.DataFrame(data=d100)
#             df_final_100 = df_final_100[df_final_100['rp'] > 0]

#             return_obj['success'] = "Data analysis complete!"
#             return_obj['warning2'] = create_rp(df_final_2)
#             return_obj['warning5'] = create_rp(df_final_5)
#             return_obj['warning10'] = create_rp(df_final_10)
#             return_obj['warning25'] = create_rp(df_final_25)
#             return_obj['warning50'] = create_rp(df_final_50)
#             return_obj['warning100'] = create_rp(df_final_100)

#             return JsonResponse(return_obj)

#         except Exception as e:
#             print(str(e))
#             return JsonResponse({'error': 'No data found for the selected reach.'})
#     else:
#         pass

# def create_rp(df_):
#     war = {}

#     list_coordinates = []
#     for lat, lon in zip(df_['lat'].tolist() , df_['lon'].tolist()):
#         list_coordinates.append([lat,lon])

#     return list_coordinates

# def ecmwf_get_time_series(request):
#     get_data = request.GET
#     try:
#         # model = get_data['model']
#         watershed = get_data['watershed']
#         subbasin = get_data['subbasin']
#         comid = get_data['comid']
#         units = 'metric'

#         '''Getting Forecast Stats'''
#         if get_data['startdate'] != '':
#             startdate = get_data['startdate']
#             res = requests.get(
#                 app.get_custom_setting('api_source') + '/api/ForecastStats/?reach_id=' + comid + '&date=' + startdate + '&return_format=csv',
#                 verify=False).content
#         else:
#             res = requests.get(
#                 app.get_custom_setting('api_source') + '/api/ForecastStats/?reach_id=' + comid + '&return_format=csv',
#                 verify=False).content

#         stats_df = pd.read_csv(io.StringIO(res.decode('utf-8')), index_col=0)
#         stats_df.index = pd.to_datetime(stats_df.index)
#         stats_df[stats_df < 0] = 0
#         stats_df.index = stats_df.index.to_series().dt.strftime("%Y-%m-%d %H:%M:%S")
#         stats_df.index = pd.to_datetime(stats_df.index)

#         hydroviewer_figure = geoglows.plots.forecast_stats(stats=stats_df, titles={'Reach ID': comid})

#         x_vals = (stats_df.index[0], stats_df.index[len(stats_df.index) - 1], stats_df.index[len(stats_df.index) - 1], stats_df.index[0])
#         max_visible = max(stats_df.max())

#         '''Getting Forecast Records'''
#         res = requests.get(
#             app.get_custom_setting('api_source') + '/api/ForecastRecords/?reach_id=' + comid + '&return_format=csv',
#             verify=False).content

#         records_df = pd.read_csv(io.StringIO(res.decode('utf-8')), index_col=0)
#         records_df.index = pd.to_datetime(records_df.index)
#         records_df[records_df < 0] = 0
#         records_df.index = records_df.index.to_series().dt.strftime("%Y-%m-%d %H:%M:%S")
#         records_df.index = pd.to_datetime(records_df.index)

#         records_df = records_df.loc[records_df.index >= pd.to_datetime(stats_df.index[0] - dt.timedelta(days=8))]
#         records_df = records_df.loc[records_df.index <= pd.to_datetime(stats_df.index[0] + dt.timedelta(days=2))]

#         if len(records_df.index) > 0:
#             hydroviewer_figure.add_trace(go.Scatter(
#                 name='1st days forecasts',
#                 x=records_df.index,
#                 y=records_df.iloc[:, 0].values,
#                 line=dict(
#                     color='#FFA15A',
#                 )
#             ))

#             x_vals = (records_df.index[0], stats_df.index[len(stats_df.index) - 1], stats_df.index[len(stats_df.index) - 1], records_df.index[0])
#             max_visible = max(max(records_df.max()), max_visible)

#         '''Getting Return Periods'''
#         res = requests.get(app.get_custom_setting('api_source') + '/api/ReturnPeriods/?reach_id=' + comid + '&return_format=csv',
#             verify=False).content
#         rperiods_df = pd.read_csv(io.StringIO(res.decode('utf-8')), index_col=0)

#         r2 = int(rperiods_df.iloc[0]['return_period_2'])

#         colors = {
#             '2 Year': 'rgba(254, 240, 1, .4)',
#             '5 Year': 'rgba(253, 154, 1, .4)',
#             '10 Year': 'rgba(255, 56, 5, .4)',
#             '20 Year': 'rgba(128, 0, 246, .4)',
#             '25 Year': 'rgba(255, 0, 0, .4)',
#             '50 Year': 'rgba(128, 0, 106, .4)',
#             '100 Year': 'rgba(128, 0, 246, .4)',
#         }

#         if max_visible > r2:
#             visible = True
#             hydroviewer_figure.for_each_trace(
#                 lambda trace: trace.update(visible=True) if trace.name == "Maximum & Minimum Flow" else (), )
#         else:
#             visible = 'legendonly'
#             hydroviewer_figure.for_each_trace(
#                 lambda trace: trace.update(visible=True) if trace.name == "Maximum & Minimum Flow" else (), )

#         def template(name, y, color, fill='toself'):
#             return go.Scatter(
#                 name=name,
#                 x=x_vals,
#                 y=y,
#                 legendgroup='returnperiods',
#                 fill=fill,
#                 visible=visible,
#                 line=dict(color=color, width=0))

#         r5 = int(rperiods_df.iloc[0]['return_period_5'])
#         r10 = int(rperiods_df.iloc[0]['return_period_10'])
#         r25 = int(rperiods_df.iloc[0]['return_period_25'])
#         r50 = int(rperiods_df.iloc[0]['return_period_50'])
#         r100 = int(rperiods_df.iloc[0]['return_period_100'])

#         hydroviewer_figure.add_trace(template('Return Periods', (r100 * 0.05, r100 * 0.05, r100 * 0.05, r100 * 0.05), 'rgba(0,0,0,0)', fill='none'))
#         hydroviewer_figure.add_trace(template(f'2 Year: {r2}', (r2, r2, r5, r5), colors['2 Year']))
#         hydroviewer_figure.add_trace(template(f'5 Year: {r5}', (r5, r5, r10, r10), colors['5 Year']))
#         hydroviewer_figure.add_trace(template(f'10 Year: {r10}', (r10, r10, r25, r25), colors['10 Year']))
#         hydroviewer_figure.add_trace(template(f'25 Year: {r25}', (r25, r25, r50, r50), colors['25 Year']))
#         hydroviewer_figure.add_trace(template(f'50 Year: {r50}', (r50, r50, r100, r100), colors['50 Year']))
#         hydroviewer_figure.add_trace(template(f'100 Year: {r100}', (r100, r100, max(r100 + r100 * 0.05, max_visible), max(r100 + r100 * 0.05, max_visible)), colors['100 Year']))

#         hydroviewer_figure['layout']['xaxis'].update(autorange=True);

#         chart_obj = PlotlyView(hydroviewer_figure)

#         context = {
#             'gizmo_object': chart_obj,
#         }

#         return render(request, '{0}/gizmo_ajax.html'.format(base_name), context)

#     except Exception as e:
#         print(str(e))
#         return JsonResponse({'error': 'No data found for the selected reach.'})


# def get_available_dates(request):
#     get_data = request.GET

#     watershed = get_data['watershed']
#     subbasin = get_data['subbasin']
#     comid = get_data['comid']
#     res = requests.get(
#         app.get_custom_setting('api_source') + '/api/AvailableDates/?region=' + watershed + '-' + subbasin,
#         verify=False)

#     data = res.json()

#     dates_array = (data.get('available_dates'))

#     # print(dates_array)

#     dates = []

#     for date in dates_array:
#         if len(date) == 10:
#             date_mod = date + '000'
#             date_f = dt.datetime.strptime(date_mod, '%Y%m%d.%H%M').strftime('%Y-%m-%d %H:%M')
#         else:
#             date_f = dt.datetime.strptime(date, '%Y%m%d.%H%M').strftime('%Y-%m-%d')
#             date = date[:-3]
#         dates.append([date_f, date, watershed, subbasin, comid])

#     dates.append(['Select Date', dates[-1][1]])
#     # print(dates)
#     dates.reverse()
#     # print(dates)

#     return JsonResponse({
#         "success": "Data analysis complete!",
#         "available_dates": json.dumps(dates)
#     })


# def get_historic_data(request):
#     """""
#     Returns ERA Interim hydrograph
#     """""

#     get_data = request.GET

#     try:
#         # model = get_data['model']
#         watershed = get_data['watershed']
#         subbasin = get_data['subbasin']
#         comid = get_data['comid']
#         units = 'metric'

#         era_res = requests.get(app.get_custom_setting('api_source') + '/api/HistoricSimulation/?reach_id=' + comid + '&return_format=csv', verify=False).content

#         simulated_df = pd.read_csv(io.StringIO(era_res.decode('utf-8')), index_col=0)
#         simulated_df[simulated_df < 0] = 0
#         simulated_df.index = pd.to_datetime(simulated_df.index)
#         simulated_df.index = simulated_df.index.to_series().dt.strftime("%Y-%m-%d")
#         simulated_df.index = pd.to_datetime(simulated_df.index)

#         '''Getting Return Periods'''
#         res = requests.get(
#             app.get_custom_setting('api_source') + '/api/ReturnPeriods/?reach_id=' + comid + '&return_format=csv',
#             verify=False).content
#         rperiods_df = pd.read_csv(io.StringIO(res.decode('utf-8')), index_col=0)

#         hydroviewer_figure = geoglows.plots.historic_simulation(simulated_df, rperiods_df, titles={'Reach ID': comid})

#         chart_obj = PlotlyView(hydroviewer_figure)

#         context = {
#             'gizmo_object': chart_obj,
#         }

#         return render(request, '{0}/gizmo_ajax.html'.format(base_name), context)

#     except Exception as e:
#         print(str(e))
#         return JsonResponse({'error': 'No historic data found for the selected reach.'})


# def get_flow_duration_curve(request):
#     get_data = request.GET

#     try:
#         # model = get_data['model']
#         watershed = get_data['watershed']
#         subbasin = get_data['subbasin']
#         comid = get_data['comid']
#         units = 'metric'

#         era_res = requests.get(app.get_custom_setting('api_source') + '/api/HistoricSimulation/?reach_id=' + comid + '&return_format=csv', verify=False).content

#         simulated_df = pd.read_csv(io.StringIO(era_res.decode('utf-8')), index_col=0)
#         simulated_df[simulated_df < 0] = 0
#         simulated_df.index = pd.to_datetime(simulated_df.index)
#         simulated_df.index = simulated_df.index.to_series().dt.strftime("%Y-%m-%d")
#         simulated_df.index = pd.to_datetime(simulated_df.index)

#         hydroviewer_figure = geoglows.plots.flow_duration_curve(simulated_df, titles={'Reach ID': comid})

#         chart_obj = PlotlyView(hydroviewer_figure)

#         context = {
#             'gizmo_object': chart_obj,
#         }

#         return render(request, '{0}/gizmo_ajax.html'.format(base_name), context)

#     except Exception as e:
#         print(str(e))
#         return JsonResponse({'error': 'No historic data found for calculating flow duration curve.'})


# def get_historic_data_csv(request):
#     """""
#     Returns ERA 5 data as csv
#     """""

#     get_data = request.GET

#     try:
#         # model = get_data['model']
#         watershed = get_data['watershed_name']
#         subbasin = get_data['subbasin_name']
#         comid = get_data['reach_id']

#         era_res = requests.get(
#             app.get_custom_setting('api_source') + '/api/HistoricSimulation/?reach_id=' + comid + '&return_format=csv',
#             verify=False).content

#         simulated_df = pd.read_csv(io.StringIO(era_res.decode('utf-8')), index_col=0)
#         simulated_df[simulated_df < 0] = 0
#         simulated_df.index = pd.to_datetime(simulated_df.index)
#         simulated_df.index = simulated_df.index.to_series().dt.strftime("%Y-%m-%d")
#         simulated_df.index = pd.to_datetime(simulated_df.index)

#         response = HttpResponse(content_type='text/csv')
#         response['Content-Disposition'] = 'attachment; filename=historic_streamflow_{0}_{1}_{2}.csv'.format(watershed, subbasin, comid)

#         simulated_df.to_csv(encoding='utf-8', header=True, path_or_buf=response)

#         return response

#     except Exception as e:
#         print(str(e))
#         return JsonResponse({'error': 'No historic data found.'})


# def get_forecast_data_csv(request):
#     """""
#     Returns Forecast data as csv
#     """""

#     get_data = request.GET

#     try:
#         # model = get_data['model']
#         watershed = get_data['watershed_name']
#         subbasin = get_data['subbasin_name']
#         comid = get_data['reach_id']
#         if get_data['startdate'] != '':
#             startdate = get_data['startdate']
#         else:
#             startdate = 'most_recent'

#         '''Getting Forecast Stats'''
#         if get_data['startdate'] != '':
#             startdate = get_data['startdate']
#             res = requests.get(
#                 app.get_custom_setting(
#                     'api_source') + '/api/ForecastStats/?reach_id=' + comid + '&date=' + startdate + '&return_format=csv',
#                 verify=False).content
#         else:
#             res = requests.get(
#                 app.get_custom_setting('api_source') + '/api/ForecastStats/?reach_id=' + comid + '&return_format=csv',
#                 verify=False).content

#         stats_df = pd.read_csv(io.StringIO(res.decode('utf-8')), index_col=0)
#         stats_df.index = pd.to_datetime(stats_df.index)
#         stats_df[stats_df < 0] = 0
#         stats_df.index = stats_df.index.to_series().dt.strftime("%Y-%m-%d %H:%M:%S")
#         stats_df.index = pd.to_datetime(stats_df.index)

#         init_time = stats_df.index[0]
#         response = HttpResponse(content_type='text/csv')
#         response['Content-Disposition'] = 'attachment; filename=streamflow_forecast_{0}_{1}_{2}_{3}.csv'.format(watershed, subbasin, comid, init_time)

#         stats_df.to_csv(encoding='utf-8', header=True, path_or_buf=response)

#         return response

#     except Exception as e:
#         print(str(e))
#         return JsonResponse({'error': 'No forecast data found.'})


# def shp_to_geojson(request):
#     get_data = request.GET

#     try:
#         model = get_data['model']
#         watershed = get_data['watershed']
#         subbasin = get_data['subbasin']

#         driver = ogr.GetDriverByName('ESRI Shapefile')
#         if model == 'LIS-RAPID':
#             reprojected_shp_path = os.path.join(
#                 app.get_custom_setting('lis_path'),
#                 '-'.join([watershed, subbasin]).replace(' ', '_'),
#                 '-'.join([watershed, subbasin, 'drainage_line']).replace(' ', '_'),
#                 '-'.join([watershed, subbasin, 'drainage_line', '3857.shp']).replace(' ', '_')
#             )
#         elif model == 'HIWAT-RAPID':
#             reprojected_shp_path = os.path.join(
#                 app.get_custom_setting('hiwat_path'),
#                 '-'.join([watershed, subbasin]).replace(' ', '_'),
#                 '-'.join([watershed, subbasin, 'drainage_line']).replace(' ', '_'),
#                 '-'.join([watershed, subbasin, 'drainage_line', '3857.shp']).replace(' ', '_')
#             )

#         if not os.path.exists(reprojected_shp_path):

#             raw_shp_path = reprojected_shp_path.replace('-3857', '')

#             raw_shp_src = driver.Open(raw_shp_path)
#             raw_shp = raw_shp_src.GetLayer()

#             in_prj = raw_shp.GetSpatialRef()

#             out_prj = osr.SpatialReference()

#             out_prj.ImportFromWkt(
#                 """
#                 PROJCS["WGS 84 / Pseudo-Mercator",
#                     GEOGCS["WGS 84",
#                         DATUM["WGS_1984",
#                             SPHEROID["WGS 84",6378137,298.257223563,
#                                 AUTHORITY["EPSG","7030"]],
#                             AUTHORITY["EPSG","6326"]],
#                         PRIMEM["Greenwich",0,
#                             AUTHORITY["EPSG","8901"]],
#                         UNIT["degree",0.0174532925199433,
#                             AUTHORITY["EPSG","9122"]],
#                         AUTHORITY["EPSG","4326"]],
#                     PROJECTION["Mercator_1SP"],
#                     PARAMETER["central_meridian",0],
#                     PARAMETER["scale_factor",1],
#                     PARAMETER["false_easting",0],
#                     PARAMETER["false_northing",0],
#                     UNIT["metre",1,
#                         AUTHORITY["EPSG","9001"]],
#                     AXIS["X",EAST],
#                     AXIS["Y",NORTH],
#                     EXTENSION["PROJ4","+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext  +no_defs"],
#                     AUTHORITY["EPSG","3857"]]
#                 """
#             )

#             coordTrans = osr.CoordinateTransformation(in_prj, out_prj)

#             reprojected_shp_src = driver.CreateDataSource(reprojected_shp_path)
#             reprojected_shp = reprojected_shp_src.CreateLayer('-'.join([watershed, subbasin,
#                                                                         'drainage_line', '3857']).encode('utf-8'),
#                                                               geom_type=ogr.wkbLineString)

#             raw_shp_lyr_def = raw_shp.GetLayerDefn()
#             for i in range(0, raw_shp_lyr_def.GetFieldCount()):
#                 field_def = raw_shp_lyr_def.GetFieldDefn(i)
#                 if field_def.name in ['COMID', 'watershed', 'subbasin']:
#                     reprojected_shp.CreateField(field_def)

#             # get the output layer's feature definition
#             reprojected_shp_lyr_def = reprojected_shp.GetLayerDefn()

#             # loop through the input features
#             in_feature = raw_shp.GetNextFeature()
#             while in_feature:
#                 # get the input geometry
#                 geom = in_feature.GetGeometryRef()
#                 # reproject the geometry
#                 geom.Transform(coordTrans)
#                 # create a new feature
#                 out_feature = ogr.Feature(reprojected_shp_lyr_def)
#                 # set the geometry and attribute
#                 out_feature.SetGeometry(geom)
#                 out_feature.SetField('COMID', in_feature.GetField(in_feature.GetFieldIndex('COMID')))
#                 # out_feature.SetField('watershed', in_feature.GetField(in_feature.GetFieldIndex('watershed')))
#                 # out_feature.SetField('subbasin', in_feature.GetField(in_feature.GetFieldIndex('subbasin')))
#                 # add the feature to the shapefile
#                 reprojected_shp.CreateFeature(out_feature)
#                 # dereference the features and get the next input feature
#                 out_feature = None
#                 in_feature = raw_shp.GetNextFeature()

#             fc = {
#                 'type': 'FeatureCollection',
#                 'features': []
#             }

#             for feature in reprojected_shp:
#                 fc['features'].append(feature.ExportToJson(as_object=True))

#             with open(reprojected_shp_path.replace('.shp', '.json'), 'w') as f:
#                 json.dump(fc, f)

#             # Save and close the shapefiles
#             raw_shp_src = None
#             reprojected_shp_src = None

#         shp_src = driver.Open(reprojected_shp_path)
#         shp = shp_src.GetLayer()

#         extent = list(shp.GetExtent())
#         xmin, ymin, xmax, ymax = extent[0], extent[2], extent[1], extent[3]

#         with open(reprojected_shp_path.replace('.shp', '.json'), 'r') as f:
#             geojson_streams = json.load(f)

#             geojson_layer = {
#                 'source': 'GeoJSON',
#                 'options': json.dumps(geojson_streams),
#                 'legend_title': '-'.join([watershed, subbasin, 'drainage_line']),
#                 'legend_extent': [xmin, ymin, xmax, ymax],
#                 'legend_extent_projection': 'EPSG:3857',
#                 'feature_selection': True
#             }

#             return JsonResponse(geojson_layer)

#     except Exception as e:
#         print(str(e))
#         return JsonResponse({'error': 'No shapefile found.'})


# def get_daily_seasonal_streamflow(request):
#     """
#     Returns daily seasonal streamflow chart for unique river ID
#     """
#     get_data = request.GET

#     try:
#         # model = get_data['model']
#         watershed = get_data['watershed']
#         subbasin = get_data['subbasin']
#         comid = get_data['comid']
#         units = 'metric'

#         era_res = requests.get(
#             app.get_custom_setting('api_source') + '/api/HistoricSimulation/?reach_id=' + comid + '&return_format=csv',
#             verify=False).content

#         simulated_df = pd.read_csv(io.StringIO(era_res.decode('utf-8')), index_col=0)
#         simulated_df[simulated_df < 0] = 0
#         simulated_df.index = pd.to_datetime(simulated_df.index)
#         simulated_df.index = simulated_df.index.to_series().dt.strftime("%Y-%m-%d")
#         simulated_df.index = pd.to_datetime(simulated_df.index)

#         dayavg_df = hydrostats.data.daily_average(simulated_df, rolling=True)

#         hydroviewer_figure = geoglows.plots.daily_averages(dayavg_df, titles={'Reach ID': comid})

#         chart_obj = PlotlyView(hydroviewer_figure)

#         context = {
#             'gizmo_object': chart_obj,
#         }

#         return render(request, '{0}/gizmo_ajax.html'.format(base_name), context)

#     except Exception as e:
#         print(str(e))
#         return JsonResponse({'error': 'No historic data found for calculating daily seasonality.'})

# def get_monthly_seasonal_streamflow(request):
#     """
#      Returns daily seasonal streamflow chart for unique river ID
#      """
#     get_data = request.GET

#     try:
#         # model = get_data['model']
#         watershed = get_data['watershed']
#         subbasin = get_data['subbasin']
#         comid = get_data['comid']
#         units = 'metric'

#         era_res = requests.get(
#             app.get_custom_setting('api_source') + '/api/HistoricSimulation/?reach_id=' + comid + '&return_format=csv',
#             verify=False).content

#         simulated_df = pd.read_csv(io.StringIO(era_res.decode('utf-8')), index_col=0)
#         simulated_df[simulated_df < 0] = 0
#         simulated_df.index = pd.to_datetime(simulated_df.index)
#         simulated_df.index = simulated_df.index.to_series().dt.strftime("%Y-%m-%d")
#         simulated_df.index = pd.to_datetime(simulated_df.index)

#         monavg_df = hydrostats.data.monthly_average(simulated_df)

#         hydroviewer_figure = geoglows.plots.monthly_averages(monavg_df, titles={'Reach ID': comid})

#         chart_obj = PlotlyView(hydroviewer_figure)

#         context = {
#             'gizmo_object': chart_obj,
#         }

#         return render(request, '{0}/gizmo_ajax.html'.format(base_name), context)

#     except Exception as e:
#         print(str(e))
#         return JsonResponse({'error': 'No historic data found for calculating monthly seasonality.'})

# def setDefault(request):
#     get_data = request.GET
#     set_custom_setting(get_data.get('ws_name'), get_data.get('model_name'))
#     return JsonResponse({'success': True})


# def get_units_title(unit_type):
#     """
#     Get the title for units
#     """
#     units_title = "m"
#     if unit_type == 'english':
#         units_title = "ft"
#     return units_title


# def forecastpercent(request):

#     # Check if its an ajax post request
#     get_data = request.GET

#     try:
#         watershed = request.GET.get('watershed')
#         subbasin = request.GET.get('subbasin')
#         comid = request.GET.get('comid')
#         date = request.GET.get('startdate')

#         '''Getting Forecast Stats'''
#         if get_data['startdate'] != '':
#             startdate = get_data['startdate']
#             res = requests.get(
#                 app.get_custom_setting(
#                     'api_source') + '/api/ForecastStats/?reach_id=' + comid + '&date=' + startdate + '&return_format=csv',
#                 verify=False).content

#             ens = requests.get(
#                 app.get_custom_setting(
#                     'api_source') + '/api/ForecastEnsembles/?reach_id=' + comid + '&date=' + startdate + '&ensemble=all&return_format=csv',
#                 verify=False).content

#         else:
#             res = requests.get(
#                 app.get_custom_setting('api_source') + '/api/ForecastStats/?reach_id=' + comid + '&return_format=csv',
#                 verify=False).content

#             ens = requests.get(
#                 app.get_custom_setting(
#                     'api_source') + '/api/ForecastEnsembles/?reach_id=' + comid + '&ensemble=all&return_format=csv',
#                 verify=False).content

#         stats_df = pd.read_csv(io.StringIO(res.decode('utf-8')), index_col=0)
#         stats_df.index = pd.to_datetime(stats_df.index)
#         stats_df[stats_df < 0] = 0
#         stats_df.index = stats_df.index.to_series().dt.strftime("%Y-%m-%d %H:%M:%S")
#         stats_df.index = pd.to_datetime(stats_df.index)

#         ensemble_df = pd.read_csv(io.StringIO(ens.decode('utf-8')), index_col=0)
#         ensemble_df.index = pd.to_datetime(ensemble_df.index)
#         ensemble_df[ensemble_df < 0] = 0
#         ensemble_df.index = ensemble_df.index.to_series().dt.strftime("%Y-%m-%d %H:%M:%S")
#         ensemble_df.index = pd.to_datetime(ensemble_df.index)

#         '''Getting Return Periods'''
#         res = requests.get(
# 	        app.get_custom_setting('api_source') + '/api/ReturnPeriods/?reach_id=' + comid + '&return_format=csv',
# 	        verify=False).content
#         rperiods_df = pd.read_csv(io.StringIO(res.decode('utf-8')), index_col=0)

#         table = geoglows.plots.probabilities_table(stats_df, ensemble_df, rperiods_df)

#         return HttpResponse(table)

#     except Exception:
#         return JsonResponse({'error': 'No data found for the selected station.'})


# def get_waterlevel_data(request):
#     """
#     Get data from telemetric stations
#     """
#     get_data = request.GET

#     try:
#         codEstacion = get_data['stationcode']
#         nomEstacion = get_data['stationname']
#         oldCodEstacion = get_data['oldcode']
#         tipoEstacion = get_data['stationtype']
#         catEstacion = get_data['stationcat']
#         statusEstacion = get_data['stationstatus']
#         river = get_data['stream']

#         tz = pytz.timezone('America/Bogota')
#         hoy = dt.datetime.now(tz)

#         end_date = dt.datetime(int(hoy.year),int(hoy.month),1)
#         ini_date = end_date - relativedelta(months=7)

#         time_array = []

#         while ini_date <= end_date:
#             time_array.append(ini_date)
#             ini_date += relativedelta(months=1)

#         if statusEstacion == "DIFERIDO":

#             fechas = []
#             values = []

#             for t in time_array:

#                 anyo = t.year
#                 mes = t.month

#                 if mes < 10:
#                     MM = '0' + str(mes)
#                 else:
#                     MM = str(mes)

#                 YYYY = str(anyo)

#                 url = 'https://www.senamhi.gob.pe/mapas/mapa-estaciones-2/_dato_esta_tipo02.php?estaciones={0}&CBOFiltro={1}{2}&t_e=H&estado={3}&cod_old={4}&cate_esta={5}&alt=263'.format(codEstacion, YYYY, MM, statusEstacion, oldCodEstacion, catEstacion)

#                 page = requests.get(url)
#                 soup = BeautifulSoup(page.content, 'html.parser')

#                 results = soup.find(id='dataTable')
#                 df_stations = pd.read_html(str(results))[0]
#                 df_stations = df_stations.loc[df_stations.index >= 2]

#                 if len(df_stations.iloc[:, 0].values) > 0:
#                     dates = df_stations.iloc[:, 0].values
#                     values_06hrs = df_stations.iloc[:, 1].values
#                     values_10hrs = df_stations.iloc[:, 2].values
#                     values_14hrs = df_stations.iloc[:, 3].values
#                     values_18hrs = df_stations.iloc[:, 4].values

#                     for i in range(0, len(dates)):
#                         fechas.append(dt.datetime(int(dates[i][0:4]), int(dates[i][5:7]), int(dates[i][8:10]), 6, 0, 0))
#                         fechas.append(dt.datetime(int(dates[i][0:4]), int(dates[i][5:7]), int(dates[i][8:10]), 10, 0, 0))
#                         fechas.append(dt.datetime(int(dates[i][0:4]), int(dates[i][5:7]), int(dates[i][8:10]), 14, 0, 0))
#                         fechas.append(dt.datetime(int(dates[i][0:4]), int(dates[i][5:7]), int(dates[i][8:10]), 18, 0, 0))
#                         if values_06hrs[i] == 'S/D':
#                             values.append(np.nan)
#                         elif float(values_06hrs[i]) >= 200:
#                             values.append(float(values_06hrs[i])/200)
#                         else:
#                             values.append(float(values_06hrs[i]))
#                         if values_10hrs[i] == 'S/D':
#                             values.append(np.nan)
#                         elif float(values_10hrs[i]) >= 200:
#                             values.append(float(values_10hrs[i])/200)
#                         else:
#                             values.append(float(values_10hrs[i]))
#                         if values_14hrs[i] == 'S/D':
#                             values.append(np.nan)
#                         elif float(values_14hrs[i]) >= 200:
#                             values.append(float(values_14hrs[i])/200)
#                         else:
#                             values.append(float(values_14hrs[i]))
#                         if values_18hrs[i] == 'S/D':
#                             values.append(np.nan)
#                         elif float(values_18hrs[i]) >= 200:
#                             values.append(float(values_18hrs[i])/200)
#                         else:
#                             values.append(float(values_18hrs[i]))

#         elif statusEstacion == "REAL":

#             fechas = []
#             values = []

#             for t in time_array:

#                 anyo = t.year
#                 mes = t.month

#                 if mes < 10:
#                     MM = '0' + str(mes)

#                 else:
#                     MM = str(mes)

#                 YYYY = str(anyo)

#                 url = 'https://www.senamhi.gob.pe/mapas/mapa-estaciones-2/_dato_esta_tipo02.php?estaciones={0}&CBOFiltro={1}{2}&t_e=H&estado={3}&cod_old={4}&cate_esta={5}&alt=101'.format(codEstacion, YYYY, MM, statusEstacion, oldCodEstacion, catEstacion)
#                 page = requests.get(url)
#                 soup = BeautifulSoup(page.content, 'html.parser')

#                 results = soup.find(id='dataTable')
#                 df_stations = pd.read_html(str(results))[0]
#                 df_stations = df_stations.loc[df_stations.index >= 2]

#                 if len(df_stations.iloc[:, 0].values) > 0:
#                     dates = df_stations.iloc[:, 0].values
#                     values_06hrs = df_stations.iloc[:, 1].values
#                     values_10hrs = df_stations.iloc[:, 2].values
#                     values_14hrs = df_stations.iloc[:, 3].values
#                     values_18hrs = df_stations.iloc[:, 4].values

#                     for i in range(0, len(dates)):
#                         fechas.append(dt.datetime(int(dates[i][0:4]), int(dates[i][5:7]), int(dates[i][8:10]), 6, 0, 0))
#                         fechas.append(dt.datetime(int(dates[i][0:4]), int(dates[i][5:7]), int(dates[i][8:10]), 10, 0, 0))
#                         fechas.append(dt.datetime(int(dates[i][0:4]), int(dates[i][5:7]), int(dates[i][8:10]), 14, 0, 0))
#                         fechas.append(dt.datetime(int(dates[i][0:4]), int(dates[i][5:7]), int(dates[i][8:10]), 18, 0, 0))
#                         if values_06hrs[i] == 'S/D':
#                             values.append(np.nan)
#                         elif float(values_06hrs[i]) >= 200:
#                             values.append(float(values_06hrs[i])/200)
#                         else:
#                             values.append(float(values_06hrs[i]))
#                         if values_10hrs[i] == 'S/D':
#                             values.append(np.nan)
#                         elif float(values_10hrs[i]) >= 200:
#                             values.append(float(values_10hrs[i])/200)
#                         else:
#                             values.append(float(values_10hrs[i]))
#                         if values_14hrs[i] == 'S/D':
#                             values.append(np.nan)
#                         elif float(values_14hrs[i]) >= 200:
#                             values.append(float(values_14hrs[i])/200)
#                         else:
#                             values.append(float(values_14hrs[i]))
#                         if values_18hrs[i] == 'S/D':
#                             values.append(np.nan)
#                         elif float(values_18hrs[i]) >= 200:
#                             values.append(float(values_18hrs[i])/200)
#                         else:
#                             values.append(float(values_18hrs[i]))

#         elif statusEstacion == "AUTOMATICA":

#             fechas = []
#             values = []
#             lluvia = []

#             for t in time_array:

#                 anyo = t.year
#                 mes = t.month

#                 if mes < 10:
#                     MM = '0' + str(mes)
#                 else:
#                     MM = str(mes)

#                 YYYY = str(anyo)

#                 url = 'https://www.senamhi.gob.pe/mapas/mapa-estaciones-2/_dato_esta_tipo02.php?estaciones={0}&CBOFiltro={1}{2}&t_e=H&estado={3}&cod_old={4}&cate_esta={5}&alt=280'.format(codEstacion, YYYY, MM, statusEstacion, oldCodEstacion, catEstacion)
#                 page = requests.get(url)
#                 soup = BeautifulSoup(page.content, 'html.parser')

#                 results = soup.find(id='dataTable')
#                 df_stations = pd.read_html(str(results))[0]
#                 df_stations = df_stations.loc[df_stations.index >= 1]

#                 if len(df_stations.iloc[:, 0].values) > 0:
#                     dates = df_stations.iloc[:, 0].values
#                     horas = df_stations.iloc[:, 1].values
#                     niveles = df_stations.iloc[:, 2].values
#                     try:
#                         precipitacion = df_stations.iloc[:, 3].values
#                     except IndexError:
#                         print('No hay datos de lluvia en esta estaci??n')

#                     for i in range(0, len(dates)):
#                         fechas.append(
#                             dt.datetime(int(dates[i][0:4]), int(dates[i][5:7]), int(dates[i][8:10]), int(horas[i][0:2]),
#                                         int(horas[i][3:5])))
#                         if niveles[i] == 'S/D':
#                             values.append(np.nan)
#                         elif float(niveles[i]) >= 100:
#                             values.append(float(niveles[i])/100)
#                         else:
#                             values.append(float(niveles[i]))
#                         try:
#                             if precipitacion[i] == 'S/D':
#                                 lluvia.append(np.nan)
#                             else:
#                                 lluvia.append(float(precipitacion[i]))
#                         except IndexError:
#                             print('No hay datos de lluvia en esta estaci??n')

#         datesObservedWaterLevel = fechas
#         observedWaterLevel = values

#         pairs = [list(a) for a in zip(datesObservedWaterLevel, observedWaterLevel)]
#         water_level_df = pd.DataFrame(pairs, columns=['Datetime', 'Water Level (m)'])

#         water_level_df.set_index('Datetime', inplace=True)
#         water_level_df.dropna(inplace=True)

#         observed_WL = go.Scatter(
#             x=water_level_df.index,
#             y=water_level_df.iloc[:, 0].values,
#             name='Observed'
#         )

#         layout = go.Layout(title='Observed Water Level',
#                            xaxis=dict(
#                                title='Dates', ),
#                            yaxis=dict(
#                                title='Water Level (m)',
#                                autorange=True),
#                            showlegend=True)

#         chart_obj = PlotlyView(
#             go.Figure(data=[observed_WL],
#                       layout=layout)
#         )

#         context = {
#             'gizmo_object': chart_obj,
#         }

#         return render(request, '{0}/gizmo_ajax.html'.format(base_name), context)

#     except Exception as e:
#         print(str(e))
#         return JsonResponse({'error': 'No  data found for the station.'})


# def get_observed_waterlevel_csv(request):
#     """
#     Get data from fews stations
#     """

#     get_data = request.GET

#     try:
#         codEstacion = get_data['stationcode']
#         nomEstacion = get_data['stationname']
#         oldCodEstacion = get_data['oldcode']
#         tipoEstacion = get_data['stationtype']
#         catEstacion = get_data['stationcat']
#         statusEstacion = get_data['stationstatus']
#         river = get_data['stream']

#         tz = pytz.timezone('America/Bogota')
#         hoy = dt.datetime.now(tz)

#         end_date = dt.datetime(int(hoy.year), int(hoy.month), 1)
#         ini_date = end_date - relativedelta(months=7)

#         time_array = []

#         while ini_date <= end_date:
#             time_array.append(ini_date)
#             ini_date += relativedelta(months=1)

#         if statusEstacion == "DIFERIDO":

#             fechas = []
#             values = []

#             for t in time_array:

#                 anyo = t.year
#                 mes = t.month

#                 if mes < 10:
#                     MM = '0' + str(mes)
#                 else:
#                     MM = str(mes)

#                 YYYY = str(anyo)

#                 url = 'https://www.senamhi.gob.pe/mapas/mapa-estaciones-2/_dato_esta_tipo02.php?estaciones={0}&CBOFiltro={1}{2}&t_e=H&estado={3}&cod_old={4}&cate_esta={5}&alt=263'.format(
#                     codEstacion, YYYY, MM, statusEstacion, oldCodEstacion, catEstacion)

#                 page = requests.get(url)
#                 soup = BeautifulSoup(page.content, 'html.parser')

#                 results = soup.find(id='dataTable')
#                 df_stations = pd.read_html(str(results))[0]
#                 df_stations = df_stations.loc[df_stations.index >= 2]

#                 if len(df_stations.iloc[:, 0].values) > 0:
#                     dates = df_stations.iloc[:, 0].values
#                     values_06hrs = df_stations.iloc[:, 1].values
#                     values_10hrs = df_stations.iloc[:, 2].values
#                     values_14hrs = df_stations.iloc[:, 3].values
#                     values_18hrs = df_stations.iloc[:, 4].values

#                     for i in range(0, len(dates)):
#                         fechas.append(dt.datetime(int(dates[i][0:4]), int(dates[i][5:7]), int(dates[i][8:10]), 6, 0, 0))
#                         fechas.append(
#                             dt.datetime(int(dates[i][0:4]), int(dates[i][5:7]), int(dates[i][8:10]), 10, 0, 0))
#                         fechas.append(
#                             dt.datetime(int(dates[i][0:4]), int(dates[i][5:7]), int(dates[i][8:10]), 14, 0, 0))
#                         fechas.append(
#                             dt.datetime(int(dates[i][0:4]), int(dates[i][5:7]), int(dates[i][8:10]), 18, 0, 0))
#                         if values_06hrs[i] == 'S/D':
#                             values.append(np.nan)
#                         elif float(values_06hrs[i]) >= 200:
#                             values.append(float(values_06hrs[i]) / 200)
#                         else:
#                             values.append(float(values_06hrs[i]))
#                         if values_10hrs[i] == 'S/D':
#                             values.append(np.nan)
#                         elif float(values_10hrs[i]) >= 200:
#                             values.append(float(values_10hrs[i]) / 200)
#                         else:
#                             values.append(float(values_10hrs[i]))
#                         if values_14hrs[i] == 'S/D':
#                             values.append(np.nan)
#                         elif float(values_14hrs[i]) >= 200:
#                             values.append(float(values_14hrs[i]) / 200)
#                         else:
#                             values.append(float(values_14hrs[i]))
#                         if values_18hrs[i] == 'S/D':
#                             values.append(np.nan)
#                         elif float(values_18hrs[i]) >= 200:
#                             values.append(float(values_18hrs[i]) / 200)
#                         else:
#                             values.append(float(values_18hrs[i]))

#         elif statusEstacion == "REAL":

#             fechas = []
#             values = []

#             for t in time_array:

#                 anyo = t.year
#                 mes = t.month

#                 if mes < 10:
#                     MM = '0' + str(mes)

#                 else:
#                     MM = str(mes)

#                 YYYY = str(anyo)

#                 url = 'https://www.senamhi.gob.pe/mapas/mapa-estaciones-2/_dato_esta_tipo02.php?estaciones={0}&CBOFiltro={1}{2}&t_e=H&estado={3}&cod_old={4}&cate_esta={5}&alt=101'.format(
#                     codEstacion, YYYY, MM, statusEstacion, oldCodEstacion, catEstacion)
#                 page = requests.get(url)
#                 soup = BeautifulSoup(page.content, 'html.parser')

#                 results = soup.find(id='dataTable')
#                 df_stations = pd.read_html(str(results))[0]
#                 df_stations = df_stations.loc[df_stations.index >= 2]

#                 if len(df_stations.iloc[:, 0].values) > 0:
#                     dates = df_stations.iloc[:, 0].values
#                     values_06hrs = df_stations.iloc[:, 1].values
#                     values_10hrs = df_stations.iloc[:, 2].values
#                     values_14hrs = df_stations.iloc[:, 3].values
#                     values_18hrs = df_stations.iloc[:, 4].values

#                     for i in range(0, len(dates)):
#                         fechas.append(dt.datetime(int(dates[i][0:4]), int(dates[i][5:7]), int(dates[i][8:10]), 6, 0, 0))
#                         fechas.append(
#                             dt.datetime(int(dates[i][0:4]), int(dates[i][5:7]), int(dates[i][8:10]), 10, 0, 0))
#                         fechas.append(
#                             dt.datetime(int(dates[i][0:4]), int(dates[i][5:7]), int(dates[i][8:10]), 14, 0, 0))
#                         fechas.append(
#                             dt.datetime(int(dates[i][0:4]), int(dates[i][5:7]), int(dates[i][8:10]), 18, 0, 0))
#                         if values_06hrs[i] == 'S/D':
#                             values.append(np.nan)
#                         elif float(values_06hrs[i]) >= 200:
#                             values.append(float(values_06hrs[i]) / 200)
#                         else:
#                             values.append(float(values_06hrs[i]))
#                         if values_10hrs[i] == 'S/D':
#                             values.append(np.nan)
#                         elif float(values_10hrs[i]) >= 200:
#                             values.append(float(values_10hrs[i]) / 200)
#                         else:
#                             values.append(float(values_10hrs[i]))
#                         if values_14hrs[i] == 'S/D':
#                             values.append(np.nan)
#                         elif float(values_14hrs[i]) >= 200:
#                             values.append(float(values_14hrs[i]) / 200)
#                         else:
#                             values.append(float(values_14hrs[i]))
#                         if values_18hrs[i] == 'S/D':
#                             values.append(np.nan)
#                         elif float(values_18hrs[i]) >= 200:
#                             values.append(float(values_18hrs[i]) / 200)
#                         else:
#                             values.append(float(values_18hrs[i]))

#         elif statusEstacion == "AUTOMATICA":

#             fechas = []
#             values = []
#             lluvia = []

#             for t in time_array:

#                 anyo = t.year
#                 mes = t.month

#                 if mes < 10:
#                     MM = '0' + str(mes)
#                 else:
#                     MM = str(mes)

#                 YYYY = str(anyo)

#                 url = 'https://www.senamhi.gob.pe/mapas/mapa-estaciones-2/_dato_esta_tipo02.php?estaciones={0}&CBOFiltro={1}{2}&t_e=H&estado={3}&cod_old={4}&cate_esta={5}&alt=280'.format(
#                     codEstacion, YYYY, MM, statusEstacion, oldCodEstacion, catEstacion)
#                 page = requests.get(url)
#                 soup = BeautifulSoup(page.content, 'html.parser')

#                 results = soup.find(id='dataTable')
#                 df_stations = pd.read_html(str(results))[0]
#                 df_stations = df_stations.loc[df_stations.index >= 1]

#                 if len(df_stations.iloc[:, 0].values) > 0:
#                     dates = df_stations.iloc[:, 0].values
#                     horas = df_stations.iloc[:, 1].values
#                     niveles = df_stations.iloc[:, 2].values
#                     try:
#                         precipitacion = df_stations.iloc[:, 3].values
#                     except IndexError:
#                         print('No hay datos de lluvia en esta estaci??n')

#                     for i in range(0, len(dates)):
#                         fechas.append(
#                             dt.datetime(int(dates[i][0:4]), int(dates[i][5:7]), int(dates[i][8:10]), int(horas[i][0:2]),
#                                         int(horas[i][3:5])))
#                         if niveles[i] == 'S/D':
#                             values.append(np.nan)
#                         elif float(niveles[i]) >= 100:
#                             values.append(float(niveles[i]) / 100)
#                         else:
#                             values.append(float(niveles[i]))
#                         try:
#                             if precipitacion[i] == 'S/D':
#                                 lluvia.append(np.nan)
#                             else:
#                                 lluvia.append(float(precipitacion[i]))
#                         except IndexError:
#                             print('No hay datos de lluvia en esta estaci??n')

#         datesObservedWaterLevel = fechas
#         observedWaterLevel = values

#         pairs = [list(a) for a in zip(datesObservedWaterLevel, observedWaterLevel)]
#         water_level_df = pd.DataFrame(pairs, columns=['Datetime', 'Water Level (m)'])

#         water_level_df.set_index('Datetime', inplace=True)
#         water_level_df.dropna(inplace=True)

#         response = HttpResponse(content_type='text/csv')
#         response['Content-Disposition'] = 'attachment; filename=observed_water_level_{0}_{1}.csv'.format(
#             codEstacion, nomEstacion)

#         water_level_df.to_csv(encoding='utf-8', header=True, path_or_buf=response)

#         return response

#     except Exception as e:
#         print(str(e))
#         return JsonResponse({'error': 'An unknown error occurred while retrieving the Water Level Data.'})
