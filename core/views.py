import os
import urllib
from datetime import datetime

import requests
from django.http import HttpResponse
from django.shortcuts import render
import pandas as pd

# Create your views here.
from .forms import DateForm
import zipfile

import redis

r = redis.from_url(os.environ.get("REDIS_URL"))


def index(request):
    link = None
    all_stocks = None
    if request.method == 'POST':
        form = DateForm(request.POST)
        if form.is_valid():
            date = form.cleaned_data['date']
            month = form.cleaned_data['month']
            year = form.cleaned_data['year']
            rep = datetime(int(year), int(month), int(date)).strftime('%d%m%y')

            match_keys = r.keys(pattern=rep + '*')
            if match_keys:
                df = pd.DataFrame(columns=['NAME', 'OPEN', 'LOW', 'HIGH', 'CLOSE'])
                for i, val in enumerate(match_keys, start=1):
                    df.loc[i] = [x.decode() for x in r.hmget(val, 'NAME', 'OPEN', 'LOW', 'HIGH', 'CLOSE')]
                # df_html = df.to_html()
                all_stocks = df.T.to_dict().values()
                return render(request, 'ui.html', {'f': form, 'link': link, 'errorText': '', 'all_stocks': all_stocks})

            link = 'https://www.bseindia.com/download/BhavCopy/Equity/EQ{}_CSV.ZIP'.format(rep)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) '
                              'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
            }
            response = requests.get(link, allow_redirects=True, headers=headers)
            if not response.ok:
                return render(request, 'ui.html', {'f': DateForm(), 'link': None,
                                                     'errorText': 'Bhavcopy not found for {}'.format(rep),
                                                     'all_stocks': []})
            with open('EQ{}.zip'.format(rep), 'wb') as f:
                f.write(response.content)

            with zipfile.ZipFile('EQ{}.zip'.format(rep), 'r') as zip_ref:
                zip_ref.extractall('.')

            df = pd.read_csv('EQ{}.csv'.format(rep))

            for _, row in df.iterrows():
                r.hmset('{}:{}'.format(rep, row['SC_NAME'].strip()),
                        {'NAME': row['SC_NAME'].strip(),
                         'OPEN': row['OPEN'],
                         'HIGH': row['HIGH'],
                         'LOW': row['LOW'],
                         'CLOSE': row['CLOSE']})
            df.rename(columns={'SC_NAME': 'NAME'}, inplace=True)
            # df_html = df[['NAME', 'OPEN', 'LOW', 'HIGH', 'CLOSE']].to_html()
            all_stocks = df[['NAME', 'OPEN', 'LOW', 'HIGH', 'CLOSE']].T.to_dict().values()

            os.remove('EQ{}.csv'.format(rep))
            os.remove('EQ{}.zip'.format(rep))

    else:
        form = DateForm()

    return render(request, 'ui.html', {'f': form, 'link': link, 'errorText': '', 'all_stocks': all_stocks})
# https://www.bseindia.com/download/BhavCopy/Equity/.ZIP

# https://www.bseindia.com/download/BhavCopy/Equity/010403_CSV.ZIP
# https://www.bseindia.com/download/BhavCopy/Equity/EQ010220_CSV.ZIP
