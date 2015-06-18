import json

import webapp2
import wsgiref.handlers
from google.appengine.ext.webapp import template
from google.appengine.api import memcache
from webapp2_extras import sessions

from models.iou import Iou, OUTSTANDING, PAID, CANCELLED
from models.user import User

import datetime # TODO delete?


USER_EMAIL = "test@example.com" # TODO delete
MESSAGES = {
    'login_failed': 'Your email or password is invalid, try going to the reset password page.',
    'not_logged_in': 'It appears you are not logged in.',
    'not_admin': 'You are attempting to access an admin page but are not admin',
    'reset_success': 'Your password has been reset.  Please check your email.',
    'reset_failed': 'Register/Password reset failed.  Did you enter valid SirsiDynix email?',
    'no_password': 'Please enter a password',
    'logged_out': 'You have been logged out',
    'cancelled': 'Iou cancelled',
    'new_success': 'Iou created',
    'paid': 'Iou(s) paid',
}

class BaseHandler(webapp2.RequestHandler):
    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)
        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session()

    def render_template(self, filename, values):
        values['user_email'] = self.session.get('email')
        values['admin'] = self.session.get('admin')
        response = template.render(filename, values)
        self.response.out.write(unicode(response))
    
    def login(self, email, admin=False):
        self.session['email'] = email
        self.session['admin'] = admin
    
    def logout(self):
        self.session['email'] = None
        self.session['admin'] = None
    
    def is_logged_in(self):
        return bool(self.session.get('email'))

class UserHandler(BaseHandler):
    def get(self):
        user_email = self.session.get('email')
        message = self.request.get('message')
        message = MESSAGES.get(message)
        if not user_email:
            self.redirect('/login?message=not_logged_in')
            return
        ious = Iou.get_outstanding(user_email)
        recents = Iou.get_recent(user_email)
        self.render_template('templates/user.html', locals())
#        response = template.render('templates/user.html', locals())
#        self.response.out.write(str(response))

class NewHandler(BaseHandler):
    def post(self):
        user_email = self.session.get('email')
        if not user_email:
            self.redirect('/login?message=not_logged_in')
            return
        amount = float(self.request.get('amount'))
        Iou.create_new(user_email, amount)
        self.redirect('/?message=new_success')

class PayHandler(BaseHandler):
    def post(self):
        user_email = self.session.get('email')
        if not user_email:
            self.redirect('/login?message=not_logged_in')
            return
        for iou_id in self.request.arguments():
            iou = Iou.get_by_key(iou_id)
            self.response.out.write(iou_id + ' got id\n')
            if not iou:
                continue
            self.response.out.write(iou_id + ' got iou\n')
            if iou.user_email != user_email:
                continue
            self.response.out.write(iou_id + ' got right email\n')
            iou.pay()
        self.redirect('/?message=paid')

class CancelHandler(BaseHandler):
    def post(self, iou_id):
        user_email = self.session.get('email')
        if not user_email:
            self.redirect('/login?message=not_logged_in')
            return
        iou = Iou.get_by_key(iou_id)
        if not iou:
            self.error(404)
            return
        if iou.user_email != user_email:
            self.error(401)
            return
        iou.cancel()
        self.redirect('/?message=cancelled')

class AdminHandler(BaseHandler):
    def get(self):
        user_email = self.session.get('email')
        message = self.request.get('message')
        message = MESSAGES.get(message)
        if not user_email:
            self.redirect('/login?message=not_logged_in')
            return
        if not self.session.get('admin'):
            self.redirect('/?message=not_admin')
            return
        outstanding = Iou.get_outstanding_all()
        payments = Iou.get_payments_recent()
        self.render_template('templates/admin.html', locals())

class LoginHandler(BaseHandler):
    def get(self):
        self.logout()
        message = self.request.get('message')
        message = MESSAGES.get(message)
        email = self.request.get('email')
        if email:
            user = User.get_by_email(email)
            pw = self.request.get('pw')
            if user.check_pw(pw):
                self.login(user.email, user.admin)
                self.redirect('/?message=login_success')
                return
        self.render_template('templates/login.html', locals())
    def post(self):
        self.logout()
        email = self.request.get('email')
        user = User.get_by_email(email)
        pw = self.request.get('pw')
        if not user or not user.check_pw(pw):
            self.redirect('/login?message=login_failed')
            return
        self.login(user.email, user.admin)
        self.redirect('/')

class LogoutHandler(BaseHandler):
    def get(self):
        self.logout()
        self.redirect('/login?message=logged_out')

class ResetHandler(BaseHandler):
    def get(self):
        self.logout()
        message = self.request.get('message')
        message = MESSAGES.get(message)
        self.render_template('templates/reset.html', locals())
    def post(self):
        self.logout()
        email = self.request.get('email')
        pw = User.reset(email)
        if not pw:
            self.redirect('/reset?message=reset_failed')
        else:
            self.redirect('/login?message=reset_success')


iou_id = r'([a-z|A-Z|0-9]+)'

config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': 'HailTorchwood',
}

app = webapp2.WSGIApplication([
    (r'/admin', AdminHandler),
    (r'/login', LoginHandler),
    (r'/logout', LogoutHandler),
    (r'/reset', ResetHandler),
    (r'/iou/new', NewHandler),
    (r'/iou/pay', PayHandler),
    (r'/iou/' + iou_id + '/cancel', CancelHandler),
    (r'/?', UserHandler),
    ],
    config=config,
    debug=False)

def main():
    wsgiref.handlers.CGIHandler().run(app)

if __name__ == "__main__":
    main()
