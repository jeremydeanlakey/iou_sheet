import datetime

from google.appengine.ext import ndb


OUTSTANDING = "outstanding"
PAID = "paid"
CANCELLED = "canceled"


def beginning_of_last_week():
    today = datetime.datetime.now()
    days_ago = 7+today.weekday()
    return (today - datetime.timedelta(days=days_ago))


class Iou(ndb.Model):
    user_email = ndb.StringProperty(required=True)
    amount = ndb.FloatProperty(required=True)
    created_date = ndb.DateTimeProperty(auto_now=True)
    status = ndb.StringProperty(default=OUTSTANDING)
    status_date = ndb.DateTimeProperty()
    
    def cancel(self):
        self.status = CANCELLED
        self.status_date = datetime.datetime.now()
        self.put()
    
    def pay(self):
        self.status = PAID
        self.status_date = datetime.datetime.now()
        self.put()
    
    def to_json(self):
        iou_json = super(Iou, self).to_dict()
        iou_json['key'] = self.key.id()
        iou_json['amount'] = '{:,.2f}'.format(self.amount)
        return iou_json
    
    @staticmethod
    def get_by_key(key):
        root_key = Iou.get_root()
        iou = Iou.get_by_id(int(key), parent=root_key)
        return iou
    
    @staticmethod
    def create_new(email, amount):
        root_key = Iou.get_root()
        new_iou = Iou(
            parent = root_key,
            user_email = email,
            amount = amount
        )
        new_iou.put()
        return new_iou
    
    @staticmethod
    def get_outstanding(email):
        root_key = Iou.get_root()
        qry = Iou.query(ancestor=root_key)
        qry = qry.filter(
            Iou.status == OUTSTANDING, 
            Iou.user_email == email
        )
        results = []
        for iou in qry.fetch():
            results.append(iou.to_json())
        return results

    @staticmethod
    def get_outstanding_all():
        root_key = Iou.get_root()
        qry = Iou.query(ancestor=root_key)
        qry = qry.filter(
            Iou.status == OUTSTANDING
        )
        results = []
        for iou in qry.fetch():
            results.append(iou.to_json())
        return results
    
    @staticmethod
    def get_recent(email):
        root_key = Iou.get_root()
        qry = Iou.query(ancestor=root_key)
        qry = qry.filter(
            # only one inequality per query, but status_date should also indicate not outstanding
            #Iou.status != OUTSTANDING, 
            Iou.status_date > beginning_of_last_week(), 
            Iou.user_email == email
        )
        results = []
        for iou in qry.fetch():
            results.append(iou.to_json())
        return results
    
    @staticmethod
    def get_payments_recent():
        root_key = Iou.get_root()
        qry = Iou.query(ancestor=root_key)
        qry = qry.filter(
            Iou.status == PAID,
            Iou.status_date > beginning_of_last_week(), 
        )
        results = []
        for iou in qry.fetch():
            results.append(iou.to_json())
        return results
    
    @staticmethod
    def get_root():
        root_key = ndb.Key('Iou','root')
        if root_key is None:
            new_root = ndb.Model(key='root')
            new_root.put()
            root_key = new_root.key[0]
        return root_key
