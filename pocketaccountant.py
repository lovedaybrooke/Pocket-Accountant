import os
import sys
for k in [k for k in sys.modules if k.startswith('django')]:
    del sys.modules[k]
from google.appengine.dist import use_library
use_library('django', '1.2')
from google.appengine.ext import db
import datetime


class Logged_spending(db.Model):
    descrip = db.StringProperty()
    amount = db.IntegerProperty()
    date = db.DateTimeProperty()

    @classmethod
    def spending_during_period(self, start):
        end = datetime.datetime(datetime.date.today().year,
            datetime.date.today().month, datetime.date.today().day, 6)
        total = 0
        spending_breakdown = ''
        spendings = Logged_spending.all().filter('date >', start).filter(
            'date <', end)
        for spending in spendings:
            spending_breakdown += "    {0} on {1}\n".format(
                Logged_spending.convert_money_to_string(spending.amount),
                spending.descrip)
            total += spending.amount
        if total == 0:
            spending_breakdown = "no spending"
        return spending_breakdown, Logged_spending.convert_money_to_string(
            total)

    @staticmethod
    def convert_money_to_string(amount):
        if amount == 0:
            pounds = '0'
            pence = '00'
        else:
            amount = str(amount)
            pence = amount[-2:]
            if len(amount) > 2:
                pounds = amount[:(len(amount)-2)]
            else:
                pounds = '0'
        return u"\xA3" + pounds + "." + pence


def correct_for_dst(today):
    spring2011 = datetime.datetime(2011, 03, 27, 1, 0)
    autumn2011 = datetime.datetime(2011, 10, 30, 2, 0)
    spring2012 = datetime.datetime(2012, 03, 25, 1, 0)
    autumn2011 = datetime.datetime(2012, 10, 28, 2, 0)
    spring2013 = datetime.datetime(2013, 03, 31, 1, 0)
    autumn2013 = datetime.datetime(2013, 10, 27, 2, 0)
    spring2014 = datetime.datetime(2014, 03, 30, 1, 0)
    autumn2014 = datetime.datetime(2014, 10, 26, 2, 0)
    spring2015 = datetime.datetime(2015, 03, 29, 1, 0)
    autumn2015 = datetime.datetime(2015, 10, 25, 2, 0)
    if today >= spring2011 and today <= autumn2011:
        return today + datetime.timedelta(0, 3600)
    else:
        return today
