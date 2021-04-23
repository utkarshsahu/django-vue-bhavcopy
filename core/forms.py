from django import forms


class DateForm(forms.Form):
    year = forms.ChoiceField(choices=[(x, x) for x in range(2001, 2022)])
    month = forms.ChoiceField(choices=[(x, x) for x in range(1, 13)])
    day = forms.ChoiceField(choices=[(x, x) for x in range(1, 32)])
