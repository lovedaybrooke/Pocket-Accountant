import logging
import urllib
import re
import string
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import mail
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
import oauth2 as oauth
import httplib2
import simplejson as json
import secrets
import pocketaccountant
import datetime

class DirectMessage(db.Model):            
    text = db.StringProperty()
    id = db.StringProperty()
    date = db.DateTimeProperty()
    
    @classmethod
    def last_DM_ID(self):
        last_DM = DirectMessage.all().order('-date').get()
        return last_DM.id
        
    @staticmethod
    def make_datetime(idatetime):
        return datetime.datetime.strptime(string.join(idatetime.split(' +0000 ')), '%a %b %d %H:%M:%S %Y')

class Process_new_DM(InboundMailHandler):
    def receive(self, mail_message):
        consumer = oauth.Consumer(key='A0YdjSUGSwKPfEEF1ThQ', secret=secrets.consumer)
        token = oauth.Token(key='371653560-dLklDiFqg8hMKOsskiF0MDmdCLOrwKhwH08vyq0E', secret=secrets.access)
        client = oauth.Client(consumer, token)
        url = 'http://api.twitter.com/1/direct_messages.json?since_id='+DirectMessage.last_DM_ID()
        resp, content = client.request(    
            url,
            method="GET",
            body=None,
            headers=None,
            force_auth_header=True
        )
        jsoncontent = json.loads(content)
        try: 
            if not jsoncontent:
               logging.error("Received an email, but there weren't any new DMs")
            else:
                i = len(jsoncontent) - 1
                while i >= 0:
                    newDM = DirectMessage()
                    newDM.id = jsoncontent[i]['id_str']
                    newDM.text = jsoncontent[i]['text']
                    newDM.date = pocketaccountant.correct_for_dst(DirectMessage.make_datetime(jsoncontent[i]['created_at']))
                    i -= 1
                    db.put(newDM)
                    
                    DMtext = jsoncontent[i]['text']
                    DMtext = DMtext.split(',')
                    spending = pocketaccountant.Logged_spending()
                    spending.amount = pocketaccountant.InputForm.money_int(DMtext[0])
                    spending.descrip = DMtext[1]
                    spending.date = pocketaccountant.correct_for_dst(DirectMessage.make_datetime(jsoncontent[i]['created_at']))
                    db.put(spending)
                    
        except Exception, message:
            url = 'http://api.twitter.com/1/direct_messages/new.json'
            resp, content = client.request(    
                url,
                method="POST",
                body='screen_name=lovedaybrooke&text='+ str(message),
                headers=None,
                force_auth_header=True
            )
        
application = webapp.WSGIApplication([
  Process_new_DM.mapping()
], debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()