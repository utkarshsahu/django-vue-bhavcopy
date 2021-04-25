import os
import zipfile
from io import BytesIO
from urllib.request import urlopen
from zipfile import ZipFile
from datetime import datetime, timedelta

import pandas as pd
import pytz
import redis
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_events
from django.utils import timezone
from django_apscheduler.models import DjangoJobExecution
import sys

from core.utils import prev_n_weekday

r = redis.from_url(os.environ.get("REDIS_URL"))


# This is the function you want to schedule - add as many as you want and
# then register them in the start() function below

def get_bhavcopy(datestring: str):

    link = 'https://www.bseindia.com/download/BhavCopy/Equity/EQ{}_CSV.ZIP'.format(datestring)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
    }
    response = requests.get(link, allow_redirects=True, headers=headers)
    return response


def delete_prev_keys_in_redis(date_obj):
    five_days_before = prev_n_weekday(date_obj, n=5).strftime('%d%m%y')
    match_keys = r.keys(pattern=five_days_before + '*')
    if match_keys:
        r.delete(*match_keys)
    else:
        print('No keys to delete!')


def download_bhavcopy():
    date_now = datetime.now(tz=pytz.timezone('Asia/Kolkata')).date()
    date_now_s = date_now.strftime('%d%m%y')

    if r.keys(pattern=(date_now_s + '*')):
        delete_prev_keys_in_redis(date_now)
        return

    response = get_bhavcopy(date_now_s)

    if not response.ok:
        print('Tried downloading bhavcopy. Didn\'t succeed')
        return

    with open('EQ{}.zip'.format(date_now_s), 'wb') as f:
        f.write(response.content)

    with zipfile.ZipFile('EQ{}.zip'.format(date_now_s), 'r') as zip_ref:
        zip_ref.extractall('.')

    print(os.listdir('.'))
    if os.path.exists('EQ{}.csv'.format(date_now_s)):
        df = pd.read_csv('./EQ{}.csv'.format(date_now_s))
    else:
        df = pd.read_csv('./EQ{}.CSV'.format(date_now_s))

    for _, row in df.iterrows():
        r.hmset('{}:{}'.format(date_now, row['SC_NAME'].strip()),
                {'NAME': row['SC_NAME'].strip(),
                 'OPEN': row['OPEN'],
                 'HIGH': row['HIGH'],
                 'LOW': row['LOW'],
                 'CLOSE': row['CLOSE']})

    if os.path.exists('EQ{}.csv'.format(date_now_s)):
        os.remove('EQ{}.csv'.format(date_now_s))
    else:
        os.remove('EQ{}.CSV'.format(date_now_s))
    os.remove('EQ{}.zip'.format(date_now_s))

    delete_prev_keys_in_redis(date_now)


def start():
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")
    # run this job every 24 hours
    scheduler.add_job(download_bhavcopy, 'cron', hour=18, minute=0, timezone='Asia/Kolkata',
                      day_of_week='mon-fri', name='clean_accounts', jobstore='default')
    register_events(scheduler)
    scheduler.start()
    print("Scheduler started...", file=sys.stdout)