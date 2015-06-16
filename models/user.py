import string, re, random

from google.appengine.api import mail
from google.appengine.ext import ndb
    
CONTACT_EMAIL = 'jeremy.lakey@gmail.com'

def random_string(n=8):
    char_set = string.ascii_uppercase + string.digits
    charlist = [random.choice(char_set) for x in range(n)]
    return ''.join(charlist)

def weekstart(day):
    dt = datetime.datetime(day.year, day.month, day.day)
    return (dt - datetime.timedelta(days=dt.weekday())).date()

def send_password_email(user_email, pw):
    message_rows = [
        'Hi,',
        '',
        'Your IOU sheet password has been (re)set.',
        '',
        'Login: %s' % user_email,
        'Password: %s' % pw,
        '',
        'You can use this shortcut link:',
        'https://iousdblue.appspot.com/login?email=%s&pw=%s' % (user_email, pw),
    ]
    message = '\n'.join(message_rows)
    subject = "IOU Sheet Password"
    mail.send_mail(CONTACT_EMAIL, user_email, subject, message)

def is_valid_sirsi_email(email):
    return bool(re.match(r'[^@]*@sirsidynix[.]com$',email))


class User(ndb.Model):
    email = ndb.StringProperty(required=True)
    password = ndb.StringProperty(required=True)
    admin = ndb.BooleanProperty(default=False)
    # TODO not implemented:
    failed_logins = ndb.IntegerProperty(default=0) 
    
    def check_pw(self, pw):
        # TODO insecure: subject to timing attacks and brute force attacks
        return self.password == pw
    
    @staticmethod
    def reset(email):
        email = email.lower()
        if not is_valid_sirsi_email(email):
            return
        user = User.get_by_email(email)
        if not user:
            root_key = User.get_root()
            user = User(
                email=email, 
                password=random_string(),
                parent=root_key
            )
        else:
            user.password = random_string()
        user.put() # TODO add root for strong consistency
        send_password_email(email, user.password)
        return user.password

    @staticmethod
    def get_root():
        root_key = ndb.Key('User','root')
        if root_key is None:
            new_root = ndb.Model(key='root')
            new_root.put()
            root_key = new_root.key[0]
        return root_key
    
    @staticmethod
    def get_by_email(email):
        if not email:
            return
        qry = User.query(ancestor=User.get_root())
        qry = qry.filter(User.email == email.lower())
        user = qry.fetch(1)
        if len(user) == 0:
            return None
        else:
            return user[0]
