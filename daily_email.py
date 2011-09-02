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


class DailyEmail(webapp.RequestHandler):
    def post(self):

        today = datetime.datetime.today()
        yesterday_6am = datetime.datetime(today.year, today.month, today.day - 1, 6, 0)
        week_start = datetime.datetime(today.year, today.month, today.day, 6, 0) - datetime.timedelta(days=datetime.datetime.weekday(today))
        
        spending_breakdown = pocketaccountant.Logged_spending.yesterday(yesterday_6am)[0]
        yesterday_total = pocketaccountant.Logged_spending.yesterday(yesterday_6am)[1]
        week_total = pocketaccountant.Logged_spending.week(week_start)
        
        message = mail.EmailMessage()
        message.sender = "yesterday@pocketaccountant.appspotmail.com"
        message.to = "katmatfield@gmail.com"
        message.body = "Yesterday's spending: " + yesterday_total + "\nWeekly spending so far: " + week_total + "\n\nBreakdown:\n" + spending_breakdown
            
            
        except Exception, message:
            template_values = {
                'error' : message
                }
            path = os.path.join(os.path.dirname(__file__),'input_form.html')
            self.response.out.write(template.render(path, template_values))
            




application = webapp.WSGIApplication(
                                     [('/daily_email', DailyEmail)],
                                     debug=True)


def main():
    run_wsgi_app(application)


if __name__ == "__main__":
    main()
    
