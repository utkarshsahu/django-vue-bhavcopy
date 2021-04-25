from datetime import timedelta


def prev_n_weekday(adate, n=1):
    adate -= timedelta(days=n)
    while adate.weekday() > 4:  # Mon-Fri are 0-4
        adate -= timedelta(days=1)
    return adate
