import string, re, random

from google.appengine.ext import ndb
    
def random_string(n=24):
    char_set = string.ascii_uppercase + string.digits
    charlist = [random.choice(char_set) for x in range(n)]
    return ''.join(charlist)

# TODO seems hacky
class LongSession(ndb.Model):
    cookie = ndb.StringProperty(required=True) 
    email = ndb.StringProperty(required=True)
    admin = ndb.BooleanProperty(default=False)
    
    @staticmethod
    def create_new(email, admin):
        email = email.lower()
        session = LongSession(cookie=random_string(), email=email, admin=admin)
        session.put()
        return session
    
    @staticmethod
    def get_by_cookie(cookie):
        if not cookie:
            return
        qry = LongSession.query()
        qry = qry.filter(LongSession.cookie == cookie)
        results = qry.fetch(1)
        if len(results) == 0:
            return None
        else:
            return results[0]
