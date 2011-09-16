import os
import sys
for k in [k for k in sys.modules if k.startswith('django')]: 
    del sys.modules[k] 
from google.appengine.dist import use_library
use_library('django', '1.2')
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import mail
import datetime
import pocketaccountant
import emailreceiver
import logging


class DailyEmail(webapp.RequestHandler):
    def get(self):
        try:
            today = datetime.datetime.today()
            yesterday_6am = datetime.datetime(today.year, today.month, today.day, 6, 0) - datetime.timedelta(days=1)
            week_start = datetime.datetime(today.year, today.month, today.day, 6, 0) - datetime.timedelta(days=datetime.datetime.weekday(today))
            month_start = datetime.datetime(today.year, today.month, 1, 6, 0)
            
            spending_breakdown = pocketaccountant.Logged_spending.spending_during_period(yesterday_6am)[0]
            yesterday_total = pocketaccountant.Logged_spending.spending_during_period(yesterday_6am)[1]
            week_total = pocketaccountant.Logged_spending.spending_during_period(week_start)[1]
            month_total = pocketaccountant.Logged_spending.spending_during_period(month_start)[1]
            
            message = mail.EmailMessage()
            message.sender = "PocketAccountant@pocketaccountant.appspotmail.com"
            message.subject = "Yesterday's spending"
            message.to = emailreceiver.address
            message.body = "Yesterday's spending: " + yesterday_total + "\nWeek's spending so far: " + week_total + "\nMonth's spending so far: " + month_total + "\n\nBreakdown:\n" + spending_breakdown
            
            message.send()
        
        except Exception, e:
            logging.error(e)


application = webapp.WSGIApplication(
                                     [('/daily_email', DailyEmail)],
                                     debug=True)


def main():
    run_wsgi_app(application)


if __name__ == "__main__":
    main()