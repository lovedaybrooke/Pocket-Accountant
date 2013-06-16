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
        for dm in model_fixtures.dms:
            DirectMessage(**dm).put()

    def tearDown(self):
        self.testbed.deactivate()

    def test__loggedspending__create(self):
        """ Test LoggedSpending.create
        actually creates the logged spending object as expected and saves to DB
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
        """ Test LoggedSpending.itemised_spending_in_period
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
        """ Test LoggedSpending.total_spending_in_period
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
        """ Test LoggedSpending.convert_money_to_string
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

    def test__directmessage__last_DM_ID(self):
        """ Test DirectMessage.last_DM_ID
        actually returns the highest DM ID in the database
        """

        last_DM_id = DirectMessage.last_DM_ID()
        self.assertEqual(last_DM_id, '9870005', last_DM_id)

    def test__directmessage__create(self):
        """ Test DirectMessage.create
        actually creates and saves a DM to the DB with all the right
        attributes – and that it can successfully retrieve those
        attributes from the json response the Twitter API gives.
        """

        json_file = open('tests/example_twitter_api_response.json').read()
        dm_list = json.loads(json_file)
        DirectMessage.create(dm_list[0])
        exists = DirectMessage.all().filter('id =', '9870006').get()
        self.assertTrue(exists,
            "DirectMessage.create method doesn't correctly make & save a DM")

    def test__directmessage__make_datetime(self):
        """ Test DirectMessage.make_datetime
        corrects transforms the kind of datestrings returned in the json
        response of the Twitter API into proper datetimes.
        """

        date_string = "Mon Jul 17 19:52:08 +0000 2012"
        date_time = DirectMessage.make_datetime(date_string)
        correct_date_time = datetime.datetime(2012, 7, 17, 19, 52, 8)

        self.assertEqual(date_time, correct_date_time)


class EndToEndTests(unittest.TestCase):

    def setUp(self):
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_datastore_v3_stub()

        # Set up just one DM, so we can use that to get the last DM ID
        DirectMessage(**model_fixtures.dms[0]).put()

    @staticmethod
    def mimic_twitterpull_get(filename):
        """ A method to mimic TwitterPull.get
        because that method calls a function that actually calls the Twitter
        API to get its JSON
        """
        # @TODO find a better way of doing this

        json_file = open(filename).read()
        dm_json = json.loads(json_file)

        if not dm_json:
            logging.info("No new DMs")
        for dm in dm_json:
            dm_obj = DirectMessage.create(dm)
            LoggedSpending.create(dm['text'], dm_obj.date)

    def test_twitter_pull_with_new_DMs(self):
        """ Test TwitterPull.get when there are new DMs to pick up
        """

        EndToEndTests.mimic_twitterpull_get(
            'tests/example_twitter_api_response.json')

        # Get the text for every DM except the first DM created in setUp()
        texts_from_dms_created = [dm.text for dm in DirectMessage.all().filter(
            'id >', "9870005").order('id').fetch(10)]
        correct_texts = ["26.99,powerdrill", "5.00 noodles for lunch",
            "10.75, after-work beers"]

        error_message = ("TwitterPull doesn't appear to be creating the right "
            "DMs.\nDMs should have the text:\n{0}\n\nDMs actually have the "
            "text:\n{1}").format("\n".join(correct_texts),
            "\n".join(texts_from_dms_created))
        self.assertEqual(texts_from_dms_created, correct_texts,
            error_message)

        descrips_from_spendings_created = [s.descrip for s in
            LoggedSpending.all().filter('date >', datetime.datetime(2013, 6,
            13)).order('date').fetch(10)]
        correct_descrips = ["powerdrill", "noodles for lunch",
            "after-work beers"]

        error_message = ("TwitterPull doesn't appear to be creating the right "
            "LoggedSpendings.\nSpendings should have the descrip:\n"
            "{0}\n\nSpendings actually have the descrip:\n{1}").format(
            "\n".join(correct_descrips),
            "\n".join(descrips_from_spendings_created))
        self.assertEqual(descrips_from_spendings_created, correct_descrips,
            error_message)

    def test_twitter_pull_with_no_new_DMs(self):
        """ Test TwitterPull.get when there are NO new DMs to pick up
        """

        EndToEndTests.mimic_twitterpull_get(
            'tests/example_empty_twitter_api_response.json')

        # Get the text for every DM except the first DM created in setUp()
        dms_created = DirectMessage.all().filter('id >', "9870005").fetch(10)

        self.assertFalse(dms_created)

if __name__ == '__main__':
    unittest.main()
