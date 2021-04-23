from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from .forms import DateForm


def index(request):
    dateform = DateForm()
    return render(request, 'days.html', {'days': [1, 2, 3], 'f': dateform})


def submit(request):
    if request.method == 'POST':
        form = DateForm(request.POST)

