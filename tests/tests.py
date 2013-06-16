# coding=utf-8
import unittest
import datetime

from google.appengine.ext import db
from google.appengine.ext import testbed

import model_fixtures
from pocketaccountant import *


#
# Tests use nosegae to set up the GAE dev environment to test against, and
# Testbed to enable testing against database entries without actually needing
# to create entries in the real DB.
#
# NoseGAE: http://farmdev.com/projects/nosegae/
# Testbed:
# https://developers.google.com/appengine/docs/python/tools/localunittesting
#
# Run with
# $ nosetests tests/tests.py -v --with-gae
#

class ModelTests(unittest.TestCase):

    def setUp(self):
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_datastore_v3_stub()

        # add in test data
        for s in model_fixtures.spending:
            LoggedSpending(**s).put()

    def tearDown(self):
        self.testbed.deactivate()

    def test__loggedspending__create(self):
        """ Test the create method of LoggedSpending actually creates the
        logged spending object as expected and saves to DB
        """

        dm_text = "26.99,powerdrill"
        dm_datetime = datetime.datetime(2013, 6, 14, 12, 52, 8)
        LoggedSpending.create(dm_text, dm_datetime)
        exists = LoggedSpending.all().filter('descrip =',
            'powerdrill').filter('amount =', 2699).filter('date =',
            dm_datetime).get()
        self.assertTrue(exists,
            "LoggedSpending.create doesn't work")

    def test__loggedspending__itemised_spending_in_period(self):
        """ Test the itemised_spending_in_period method of LoggedSpending
        correctly puts together a string of the spending between today at 6am
        and the provided start-date
        """

        thurs_start = datetime.datetime(2013, 6, 13, 6)
        correct_thurs_spending = ("    £4.50 on Lunch on thursday\n"
            "    £45.00 on Theatre tickets\n"
            "    £23.45 on Noodle street takeaway\n")
        thurs_spending = LoggedSpending.itemised_spending_in_period(
            thurs_start)

        error_message = ("LoggedSpending.itemised_spending_in_period "
            "calculates spending incorrectly.\nMethod returns:\n"
            "{0}\nMethod should return:\n{1}").format(
            thurs_spending, correct_thurs_spending)

        self.assertEqual(correct_thurs_spending, thurs_spending,
            error_message)

    def test__loggedspending__total_spending_in_period(self):
        """ Test the total_spending_in_period method of LoggedSpending
        correctly calculates the total spending between today at 6am
        and the provided start-date and returns as a nicely-formatted string
        """

        thurs_start = datetime.datetime(2013, 6, 13, 6)
        correct_thurs_total = '£72.95'
        thurs_total = LoggedSpending.total_spending_in_period(
            thurs_start)

        error_message = ("LoggedSpending.total_spending_in_period "
            "calculates spending incorrectly.\nMethod returns: {0}\n"
            "Method should return:{1}\n").format(
            thurs_total, correct_thurs_total)

        self.assertEqual(correct_thurs_total, thurs_total,
            error_message)

    def test__loggedspending__test_convert_money_to_string(self):
        """ Test the convert_money_to_string method of LoggedSpending
        correctly converts an integer into a nicely-formatted string
        """

        pence_only = 34
        pence_only_str = '£0.34'
        self.assertEqual(pence_only_str,
            LoggedSpending.convert_money_to_string(pence_only),
            ("LoggedSpending.convert_money_to_string doesn't correctly convert"
            " sums of less than one pound"))

        pounds_only = 2000
        pounds_only_str = '£20.00'
        self.assertEqual(pounds_only_str,
            LoggedSpending.convert_money_to_string(pounds_only),
            ("LoggedSpending.convert_money_to_string doesn't correctly convert"
            " sums of whole pounds and no pence"))

        pounds_and_pence = 345
        pounds_and_pence_str = '£3.45'
        self.assertEqual(pounds_and_pence_str,
            LoggedSpending.convert_money_to_string(pounds_and_pence),
            ("LoggedSpending.convert_money_to_string doesn't correctly convert"
            " sums of pounds and pence"))


if __name__ == '__main__':
    unittest.main()