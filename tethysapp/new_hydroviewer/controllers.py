from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from tethys_sdk.gizmos import *
from django.http import HttpResponse, JsonResponse
from tethys_sdk.permissions import has_permission
from tethys_sdk.base import TethysAppBase
from tethys_sdk.gizmos import PlotlyView
from tethys_sdk.workspaces import app_workspace
from tethys_sdk.gizmos import Button, DatePicker, PlotlyView, SelectInput
from tethys_sdk.routing import controller
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

@controller(name='home', url='new-hydroviewer')
def home(request):
    # ecmf_object =  Ecmf()
    basic_settings = ecmf_object.get_start_custom_settings(request)
    dates_watershed = ecmf_object.get_available_dates_watershed(request)

    context = basic_settings


    return render(request, 'new_hydroviewer/home.html', context)
    # return render(request, 'hydroviewer/ecmwf.html', context)

@controller(name='get-warning-points-ecmwf', url='get-warning-points-ecmwf')
def get_warning_points(request):
    # ecmf_object =  Ecmf()
    warning_points = ecmf_object.get_warning_points(request)
    return JsonResponse(warning_points)

@controller(name='ecmwf-get-time-series', url='ecmwf-get-time-series')
def ecmwf_get_time_series(request):
    hydroviewer_figure = ecmf_object.ecmwf_get_time_series(request);
    chart_obj = PlotlyView(hydroviewer_figure)

    context = {
        'gizmo_object': chart_obj,
    }
    return render(request, f'{base_name}/gizmo_ajax.html', context)

@controller(name='get-historic-data', url='get-historic-data')
def get_historic_data(request):
    hydroviewer_figure = ecmf_object.get_historic_data(request);
    chart_obj = PlotlyView(hydroviewer_figure)
    context = {
        'gizmo_object': chart_obj,
    }
    return render(request, f'{base_name}/gizmo_ajax.html', context)


@controller(name='get-flow-duration-curve', url='get-flow-duration-curve')
def get_flow_duration_curve(request):
    hydroviewer_figure = ecmf_object.get_flow_duration_curve(request);
    chart_obj = PlotlyView(hydroviewer_figure)
    context = {
        'gizmo_object': chart_obj,
    }
    return render(request, f'{base_name}/gizmo_ajax.html', context)


@controller(name='get-daily-seasonal-streamflow', url='get-daily-seasonal-streamflow')
def get_daily_seasonal_streamflow(request):
    hydroviewer_figure = ecmf_object.get_daily_seasonal_streamflow(request);
    chart_obj = PlotlyView(hydroviewer_figure)
    context = {
        'gizmo_object': chart_obj,
    }
    return render(request, f'{base_name}/gizmo_ajax.html', context)

@controller(name='get-monthly-seasonal-streamflow', url='get-monthly-seasonal-streamflow')
def get_monthly_seasonal_streamflow(request):
    hydroviewer_figure = ecmf_object.get_monthly_seasonal_streamflow(request);
    chart_obj = PlotlyView(hydroviewer_figure)
    context = {
        'gizmo_object': chart_obj,
    }
    return render(request, f'{base_name}/gizmo_ajax.html', context)
    
@controller(name='get-forecast-percent', url='get-forecast-percent')
def get_forecast_percent(request):
    table = ecmf_object.get_forecast_percent(request);
    return HttpResponse(table)
