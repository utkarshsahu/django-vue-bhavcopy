from django import forms
from django.core.exceptions import ValidationError
from datetime import datetime


class DateForm(forms.Form):
    year = forms.ChoiceField(choices=[(x, x) for x in range(2001, 2022)])
    month = forms.ChoiceField(choices=[(x, x) for x in range(1, 13)])
    date = forms.ChoiceField(choices=[(x, x) for x in range(1, 32)])

    def clean(self):
        cleaned_data = super(DateForm, self).clean()
        year = cleaned_data.get('year')
        month = cleaned_data.get('month')
        date = cleaned_data.get('date')

        try:
            datetime(int(year), int(month), int(date))
        except ValueError:
            raise ValidationError('Invalid date entered')
        except TypeError:
            cleaned_data['year'] = '2001'
            cleaned_data['month'] = '1'
            cleaned_data['date'] = '1'

        return cleaned_data
