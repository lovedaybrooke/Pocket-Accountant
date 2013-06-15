import os
import sys
import datetime
import logging

from google.appengine.ext import db
from google.appengine.api import mail

from pocketaccountant import *
import emailreceiver


class DailyEmail(webapp2.RequestHandler):
    def get(self):
        today = datetime.datetime.today()
        today_6am = datetime.datetime.today()

        yesterday_6am =  today_6am - datetime.timedelta(days=1)
        breakdown = Logged_spending.itemised_spending_in_period(
            yesterday_6am)
        yesterday_total = Logged_spending.total_spending_in_period(
            yesterday_6am)

        week_start =  today_6am - datetime.timedelta(
            days=datetime.datetime.weekday(today))
        week_total = Logged_spending.total_spending_in_period(week_start)

        month_start = datetime.datetime(today.year, today.month, 1, 6, 0)
        month_total = Logged_spending.total_spending_in_period(
            month_start)

        message = mail.EmailMessage()
        message.sender = ("PocketAccountant@"
            "pocketaccountant.appspotmail.com")
        message.subject = "Yesterday's spending"
        message.to = emailreceiver.address
        message.body = ("Yesterday's spending: {0}\n"
            "Week's spending so far: {1}\n"
            "Month's spending so far: {2}\n\n"
            "Breakdown:{3}\n").format(yesterday_total, week_total,
            month_total, breakdown)
        message.send()

application = webapp2.WSGIApplication([('/daily_email', DailyEmail)],
                                     debug=True)