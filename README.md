Pocket Accountant
=================

Pocket Accountant is a tiny spending-tracking app, built using [Google App Engine](https://developers.google.com/appengine/docs/python). I built it because I really lack a gut-feel sense of how much I've spent so far per month or per week, which was making it hard to stick to a budget.

The app accepts DM input and uses that to store details on what you've been spending, then email you a daily summary. So, throughout the day I'll DM the app a short note on each purchase. Then, at about 7am the next day, it'll send me an email report of what I've spent so far this month, with a breakdown of yesterday's spending.

## Getting it working

### Setting up a GAE app

The app's built off GAE so, to get it working, you'll need to download the [GAE SDK](https://developers.google.com/appengine/downloads#Google_App_Engine_SDK_for_Python), add it as an app in the launcher, and then [register the app](https://developers.google.com/appengine/docs/python/gettingstartedpython27/uploading).
It doesn't really matter what you call the app since you'll never need to access any URLs or email it, but do remember to update the app.yaml with whatever you've chosen.

### The Twitter bits

Pocket Accountant works by having a Twitter 'receiver' account, to which all DMs are directed. You'll need to set one up - you can't use an existing one. You'll also need a 'sender' Twitter account from which you'll be sending DMs with information about your spending; it makes most sense for this to be your normal Twitter account. It cannot be the same as the receiver account. The sender account must follow the receiver account.

### Secrets.py

In this file you'll need the following:
consumer_key = "{{ the consumer key from your receiver twitter account }}"
consumer_secret = "{{ the consumer secret from your receiver twitter account }}"
access_key = "{{ the access token from your receiver twitter account }}"
access_secret = "{{ the access token secret from your receiver twitter account }}"
sender_address = "{{ the email address your app will be sending from }}"
receiver_address = "{{ the address to which you'd like the daily email reports sent }}"
day_starts_at = {{ integer of the hour at which you'd like yesterday to flip over to today – see 'timing' section below }}

The sender_address has to either be the email address of a registered administrator for the application (set these up in the admin console of your GAE app) or a valid app email address. Valid app email addresses are in this format:
{{ anything }}@{{ app name }}.appspotmail.com

## How it works

At 5am each day, a cron job makes a request to the Twitter API for any new DMs sent to the receiver account. All the DMs received back are added to the database as DM objects, then processed and added as LoggedSpending objects. Storing the DMs is partly a back-up, and partly so it's easy to find out the last DM id received, and thus tailor the API call.

An hour after this Twitter grab has happened, another cron job starts. It looks over the LoggedSpending in the database to calculate how much was spent yesterday (calculated from 6am yesterday to 6am today), how much this week so far, how much this month so far. The process also gets details on the exact purchases made yesterday. It puts all of that information into an email, and sends it out to the receiver address specified in secrets.py.

(To be really literal, the two cron jobs both make get requests to URLs, which kicks off the right activity.)

### Timing

5 o'clock was chosen as a sensible point to flip over between yesterday and today – I never get up earlier than that, and if I go out, I almost invariably get home by this point. The timing of the Twitter grab and email sending process are based upon this. I've not bothered making the app adaptable to daylight savings time as 5am or 6am doesn't make much difference to me.

The 5am time preference is stored in two places, which both need to be changed to alter the timing:
1) the day_starts_at number in secrets.py
2) the hours specified for the two cron jobs to run in cron.yaml

### Valid inputs

The app accepts input only via DM, and only in a certain format: the amount spent, followed by a short description of what it was spent on.

#### Valid:

1.25, newspaper
1.25 newspaper
1.25,newspaper

#### Invalid:

£1.25, newspaper
125, newspaper
1.25; newspaper
1.25 - newspaper
