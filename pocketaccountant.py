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
        

class Logged_spending(db.Model):
    descrip = db.StringProperty()
    amount = db.IntegerProperty()
    date = db.DateTimeProperty()
    
    @classmethod         
    def spending_during_period(self, start):
        end = datetime.datetime(datetime.date.today().year, datetime.date.today().month, datetime.date.today().day, 6)
        total = 0
        spending_breakdown = ''
        spendings = Logged_spending.all().filter('date >', start).filter('date <', end)
        for spending in spendings:
            spending_breakdown += "    " + Logged_spending.convert_money_to_string(spending.amount) + " on" + spending.descrip + "\n"
            total += spending.amount
        if total == 0:
            spending_breakdown = "no spending"
        return spending_breakdown, Logged_spending.convert_money_to_string(total)
 
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
    spring2011 = datetime.datetime(2011,03,27,1,0)
    autumn2011 = datetime.datetime(2011,10,30,2,0)
    spring2012 = datetime.datetime(2012,03,25,1,0)
    autumn2011 = datetime.datetime(2012,10,28,2,0)
    spring2013 = datetime.datetime(2013,03,31,1,0)
    autumn2013 = datetime.datetime(2013,10,27,2,0)
    spring2014 = datetime.datetime(2014,03,30,1,0)
    autumn2014 = datetime.datetime(2014,10,26,2,0)
    spring2015 = datetime.datetime(2015,03,29,1,0)
    autumn2015 = datetime.datetime(2015,10,25,2,0)
    if today >= spring2011 and today <= autumn2011:
        return today + datetime.timedelta(0,3600)
    else:
        return today
        

class InputForm(webapp.RequestHandler):
    def get(self):

        path = os.path.join(os.path.dirname(__file__),'input_form.html')
        self.response.out.write(template.render(path, {}))
    
    def post(self):
        try: 
            spending = Logged_spending()
            spending.descrip = self.request.get('descrip')     
            spending.amount = InputForm.money_int(self.request.get('amount'))
            spending.category = self.request.get('category')
            spending.date = correct_for_dst(datetime.datetime.today())
            db.put(spending)
            path = os.path.join(os.path.dirname(__file__),'input_form.html')
            self.response.out.write(template.render(path, {}))
            
            
        except Exception, message:
            template_values = {
                'error' : message
                }
            path = os.path.join(os.path.dirname(__file__),'input_form.html')
            self.response.out.write(template.render(path, template_values))
    
    @staticmethod
    def money_int(string):
        return int(''.join(string.split('.')))


application = webapp.WSGIApplication(
                                     [('/', InputForm)],
                                     debug=True)


def main():
    run_wsgi_app(application)


if __name__ == "__main__":
    main()