import os
import sys
import datetime
import logging

for k in [k for k in sys.modules if k.startswith('django')]:
    del sys.modules[k]
from google.appengine.dist import use_library
use_library('django', '1.2')
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import mail

from pocketaccountant import *
import emailreceiver
import traceback


class DailyEmail(webapp.RequestHandler):
    def get(self):
        try:
            today = datetime.datetime.today()
            yesterday_6am = datetime.datetime(today.year, today.month,
                today.day, 6, 0) - datetime.timedelta(days=1)
            week_start = datetime.datetime(today.year, today.month, today.day,
                6, 0) - datetime.timedelta(
                days=datetime.datetime.weekday(today))
            month_start = datetime.datetime(today.year, today.month, 1, 6, 0)

            spending_breakdown = Logged_spending.spending_during_period(
                yesterday_6am)[0]
            yesterday_total = Logged_spending.spending_during_period(
                yesterday_6am)[1]
            week_total = Logged_spending.spending_during_period(week_start)[1]
            month_total = Logged_spending.spending_during_period(
                month_start)[1]

            message = mail.EmailMessage()
            message.sender = ("PocketAccountant@"
                "pocketaccountant.appspotmail.com")
            message.subject = "Yesterday's spending"
            message.to = emailreceiver.address
            message.body = ("Yesterday's spending: {0}\n"
                "Week's spending so far: {1}\n"
                "Month's spending so far: {2}\n\n"
                "Breakdown:{3}\n").format(yesterday_total, week_total,
                month_total, spending_breakdown)
            message.send()

        except Exception:
            stacktrace = traceback.format_exc()
            logging.error("%s", stacktrace)

application = webapp.WSGIApplication(
                                     [('/daily_email', DailyEmail)],
                                     debug=True)


def main():
    run_wsgi_app(application)


if __name__ == "__main__":
    main()
