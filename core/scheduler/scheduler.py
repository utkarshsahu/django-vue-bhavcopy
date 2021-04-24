# from io import BytesIO
# from urllib.request import urlopen
# from zipfile import ZipFile
#
# from apscheduler.schedulers.background import BackgroundScheduler
# from django_apscheduler.jobstores import DjangoJobStore, register_events
# from django.utils import timezone
# from django_apscheduler.models import DjangoJobExecution
# import sys
#
#
# # This is the function you want to schedule - add as many as you want and
# # then register them in the start() function below
# def deactivate_expired_accounts():
#     link = 'https://www.bseindia.com/download/BhavCopy/Equity/EQ210420_CSV.ZIP'
#     resp = urlopen(link)
#     zipfile = ZipFile(BytesIO(resp.read()))
#     for line in zipfile.open('EQ210420.CSV').readlines():
#         print(line.decode('utf-8'))
#
#
# def start():
#     scheduler = BackgroundScheduler()
#     scheduler.add_jobstore(DjangoJobStore(), "default")
#     # run this job every 24 hours
#     scheduler.add_job(deactivate_expired_accounts, 'interval', minutes=1, name='clean_accounts', jobstore='default')
#     register_events(scheduler)
#     scheduler.start()
#     print("Scheduler started...", file=sys.stdout)


# runapscheduler.py
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django.core.management.base import BaseCommand
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution

logger = logging.getLogger(__name__)


def my_job():
    #  Your job processing logic here...
    pass


def delete_old_job_executions(max_age=604_800):
    """This job deletes all apscheduler job executions older than `max_age` from the database."""
    DjangoJobExecution.objects.delete_old_job_executions(max_age)


class Command(BaseCommand):
    help = "Runs apscheduler."

    def handle(self, *args, **options):
        scheduler = BackgroundScheduler()
        scheduler.add_jobstore(DjangoJobStore(), "default")

        scheduler.add_job(
            my_job,
            trigger=CronTrigger(second="*/10"),  # Every 10 seconds
            id="my_job",  # The `id` assigned to each job MUST be unique
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Added job 'my_job'.")

        scheduler.add_job(
            delete_old_job_executions,
            trigger=CronTrigger(
                day_of_week="mon", hour="00", minute="00"
            ),  # Midnight on Monday, before start of the next work week.
            id="delete_old_job_executions",
            max_instances=1,
            replace_existing=True,
        )
        logger.info(
            "Added weekly job: 'delete_old_job_executions'."
        )

        try:
            logger.info("Starting scheduler...")
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Stopping scheduler...")
            scheduler.shutdown()
            logger.info("Scheduler shut down successfully!")