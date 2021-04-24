from datetime import datetime

from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from .forms import DateForm


def index(request):
    link = None
    if request.method == 'POST':
        form = DateForm(request.POST)
        if form.is_valid():
            date = form.cleaned_data['date']
            month = form.cleaned_data['month']
            year = form.cleaned_data['year']
            rep = datetime(int(year), int(month), int(date)).strftime('%d%m%y')

            link = 'https://www.bseindia.com/download/BhavCopy/Equity/EQ{}_CSV.ZIP'.format(rep)
    else:
        form = DateForm()

    return render(request, 'days.html', {'f': form, 'link': link})


# https://www.bseindia.com/download/BhavCopy/Equity/010403_CSV.ZIP
# https://www.bseindia.com/download/BhavCopy/Equity/EQ010220_CSV.ZIP