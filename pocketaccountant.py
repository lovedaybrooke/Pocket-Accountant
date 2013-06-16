# coding=utf-8

# Adding lib/ to the PYTHONPATH so I can use that dir to store external
# libraries
import os, sys
lib_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'lib')
sys.path.insert(0, lib_path)

import datetime
import logging

from google.appengine.ext import db
from google.appengine.api import mail
import webapp2
import oauth2 as oauth
import simplejson as json

import secrets
import emailreceiver


class LoggedSpending(db.Model):
    descrip = db.StringProperty()
    amount = db.IntegerProperty()
    date = db.DateTimeProperty()

    @classmethod
    def create(cls, dm_text, dm_date):
        spending = LoggedSpending()
        # there are two possible formats for this:
        # 1) 1.20, fruit on monday
        # 2) 1.20,fruit on monday
        # 3) 1.20 fruit on monday
        # Detect which of these it is, and split accordingly to end up with
        # a list where the first item is the amount, the second the descrip
        if ', ' in dm_text:
            dm_split = dm_text.split(', ')
        elif ',' in dm_text:
            dm_split = dm_text.split(',')
        else:
            entire_split = dm_text.split(' ')
            dm_split = [entire_split[0],
                ' '.join(entire_split[1:])]

        spending.descrip = dm_split[1]
        spending.amount = int("".join(dm_split[0].split('.')))
        spending.date = dm_date
        spending.put()

    @classmethod
    def itemised_spending_in_period(self, start):
        """ Put together a string listing all the transaction details
        between the start date and today, 6am
        """

        today = datetime.date.today()
        end = datetime.datetime(today.year, today.month, today.day, 6)

        any_transactions = False

        spending_breakdown = ''
        spendings = LoggedSpending.all().filter('date >', start).filter(
            'date <', end)
        for spending in spendings:
            spending_breakdown += "    {0} on {1}\n".format(
                LoggedSpending.convert_money_to_string(spending.amount),
                spending.descrip)
            any_transactions = True

        if not any_transactions:
            spending_breakdown = "No spending"

        return spending_breakdown

    @classmethod
    def total_spending_in_period(cls, start):
        """ Return a total for all the spending since start to today 6am """

        today = datetime.datetime.today()
        end = datetime.datetime(today.year, today.month, today.day, 6)

        total = 0
        spendings = LoggedSpending.all().filter('date >', start).filter(
            'date <', end)
        for spending in spendings:
            total += spending.amount

        return LoggedSpending.convert_money_to_string(total)

    @staticmethod
    def convert_money_to_string(amount):
        """ Convert the amount (stored in pence) into a string like 2.50 """

        if amount == 0:
            pounds = '0'
            pence = '00'
        else:
            amount = str(amount)
            pence = amount[-2:]
            # check if any pound figures have been given. If not, insert a 0.
            if len(amount) > 2:
                pounds = amount[:(len(amount) - 2)]
            else:
                pounds = '0'

        return ("£{0}.{1}".format(pounds, pence))


class DirectMessage(db.Model):
    text = db.StringProperty()
    id = db.StringProperty()
    date = db.DateTimeProperty()

    @classmethod
    def last_DM_ID(self):
        last_DM = DirectMessage.all().order('-date').get()
        return last_DM.id

    @classmethod
    def create(cls, dm_json):
        newDM = DirectMessage()
        newDM.id = dm_json['id_str']
        newDM.text = dm_json['text']
        newDM.date = DirectMessage.make_datetime(dm_json['created_at'])
        db.put(newDM)
        return newDM

    @staticmethod
    def make_datetime(date_string):
        """ Convert the date string from the twitter json (eg "Fri Jun 14
        20:52:08 +0000 2013" to a datetime
        """

        return datetime.datetime.strptime(" ".join(date_string.split(
            ' +0000 ')), '%a %b %d %H:%M:%S %Y')


class TwitterPull(webapp2.RequestHandler):
    def get(self):
        """ Get the latest DMs from the Twitter API, make them into dm and
        logged spending objects
        """

        dm_json = TwitterPull.get_dm_json()
        if not dm_json:
            logging.info("No new DMs")
        for dm in dm_json:
            dm_obj = DirectMessage.create(dm)
            LoggedSpending.create(dm['text'], dm_obj.date)

    @classmethod
    def get_dm_json(cls):
        """ Request the most recent DMs since the last pull from the Twitter
        API, and return the response as json
        """

        consumer = oauth.Consumer(key='A0YdjSUGSwKPfEEF1ThQ',
            secret=secrets.consumer)
        token = oauth.Token(
            key='371653560-dLklDiFqg8hMKOsskiF0MDmdCLOrwKhwH08vyq0E',
            secret=secrets.access)
        client = oauth.Client(consumer, token)
        url = ('http://api.twitter.com/1.1/direct_messages'
            '.json?since_id=' + DirectMessage.last_DM_ID())
        resp, content = client.request(url,
            method="GET",
            body=None,
            headers=None,
            force_auth_header=True)
        return json.loads(content)


class DailyEmail(webapp2.RequestHandler):
    def get(self):
        """ Get all the information needed for the daily email, make & send
        the email
        """

        today = datetime.datetime.today()
        today_6am = datetime.datetime(today.year, today.month, today.day, 6, 0)

        yesterday_6am = today_6am - datetime.timedelta(days=1)
        breakdown = LoggedSpending.itemised_spending_in_period(
            yesterday_6am)
        yesterday_total = LoggedSpending.total_spending_in_period(
            yesterday_6am)

        week_start = today_6am - datetime.timedelta(
            days=datetime.datetime.weekday(today))
        week_total = LoggedSpending.total_spending_in_period(week_start)

        month_start = datetime.datetime(today.year, today.month, 1, 6, 0)
        month_total = LoggedSpending.total_spending_in_period(month_start)

        message = mail.EmailMessage()
        message.sender = ("PocketAccountant@"
            "pocketaccountant.appspotmail.com")
        message.subject = "Yesterday's spending: {0}".format(yesterday_total)
        message.to = emailreceiver.address
        message.body = ("Yesterday's spending: {0}\n"
            "Week's spending so far: {1}\n"
            "Month's spending so far: {2}\n\n"
            "Breakdown: {3}\n").format(yesterday_total, week_total,
            month_total, breakdown)
        message.send()

application = webapp2.WSGIApplication([('/daily_email', DailyEmail),
                                      ('/twitterpull', TwitterPull)],
                                     debug=True)
