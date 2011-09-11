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
        bodies = mail_message.bodies('text/plain')
        for body in bodies:
            payload = body[1]
            decodedpayload = payload.decode()
            logging.info(decodedpayload)
        
application = webapp.WSGIApplication([
  Process_new_DM.mapping()
], debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()