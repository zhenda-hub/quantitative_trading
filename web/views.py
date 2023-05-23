import pdb

from django.shortcuts import render, redirect
import pandas_datareader as pdr
from django.utils.timezone import now


# Create your views here.
def index(request):
    # return render(request, 'index.html')
    # return render(request, 'index2.html')
    return render(request, 'index3.html')


def large_plate(request):
    print('fsdfdsfsdf')
    # pdb.set_trace()
    # df = pdr.get_data_yahoo(symbols='600519', end=now())
    # df_html = df.to_html()
    # return render(request, 'large_plate.html', {'df_html': df_html})
    return render(request, 'large_plate.html')


def industry(request):
    pass