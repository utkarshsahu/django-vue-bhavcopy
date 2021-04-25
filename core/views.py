import os
from datetime import datetime

import pytz
import requests
from django.core.exceptions import ValidationError
from django.shortcuts import render
import pandas as pd

from .forms import DateForm
import zipfile

import redis

from .utils import prev_n_weekday

r = redis.from_url(os.environ.get("REDIS_URL"))


def index(request):
    if request.method == 'POST':
        form = DateForm(request.POST)
        if form.is_valid():
            date = form.cleaned_data['date']
            month = form.cleaned_data['month']
            year = form.cleaned_data['year']
            rep = datetime(int(year), int(month), int(date))
            return render_date(request, rep, form)

    else:
        form = DateForm()
        rep = prev_n_weekday(datetime.now(tz=pytz.timezone('Asia/Kolkata')).date(), n=0)
        return render_date(request, rep, form)
    return render(request, 'ui.html', {'f': form, 'errorText': 'Date is not valid!'})


def render_date(request, date_obj, form):
    date_s = date_obj.strftime('%d%m%y')
    formatted_date = date_obj.strftime('%d/%m/%Y')
    match_keys = r.keys(pattern=date_s + '*')
    context = {'f': form, 'errorText': ''}
    if match_keys:
        df = pd.DataFrame(columns=['NAME', 'OPEN', 'LOW', 'HIGH', 'CLOSE'])
        for i, val in enumerate(match_keys, start=1):
            df.loc[i] = [x.decode() for x in r.hmget(val, 'NAME', 'OPEN', 'LOW', 'HIGH', 'CLOSE')]
        all_stocks = df.T.to_dict().values()
        context.update({'all_stocks': all_stocks, 'currentDate': formatted_date})
        return render(request, 'ui.html', context)
    else:
        link = 'https://www.bseindia.com/download/BhavCopy/Equity/EQ{}_CSV.ZIP'.format(date_s)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
        }
        response = requests.get(link, allow_redirects=True, headers=headers)
        if not response.ok:
            context.update({'errorText': 'Bhavcopy not found for {}'.format(formatted_date),
                            'all_stocks': []})
            return render(request, 'ui.html', context)
        with open('EQ{}.zip'.format(date_s), 'wb') as f:
            f.write(response.content)

        with zipfile.ZipFile('EQ{}.zip'.format(date_s), 'r') as zip_ref:
            zip_ref.extractall('.')
        print(os.listdir('.'))

        if os.path.exists('EQ{}.csv'.format(date_s)):
            df = pd.read_csv('./EQ{}.csv'.format(date_s))
        else:
            df = pd.read_csv('./EQ{}.CSV'.format(date_s))

        for _, row in df.iterrows():
            r.hmset('{}:{}'.format(date_s, row['SC_NAME'].strip()),
                    {'NAME': row['SC_NAME'].strip(),
                     'OPEN': row['OPEN'],
                     'HIGH': row['HIGH'],
                     'LOW': row['LOW'],
                     'CLOSE': row['CLOSE']})

        df.rename(columns={'SC_NAME': 'NAME'}, inplace=True)
        all_stocks = df[['NAME', 'OPEN', 'LOW', 'HIGH', 'CLOSE']].T.to_dict().values()

        if os.path.exists('EQ{}.csv'.format(date_s)):
            os.remove('EQ{}.csv'.format(date_s))
        else:
            os.remove('EQ{}.CSV'.format(date_s))
        os.remove('EQ{}.zip'.format(date_s))

        context.update({'currentDate': formatted_date, 'all_stocks': all_stocks})
        return render(request, 'ui.html', context)

