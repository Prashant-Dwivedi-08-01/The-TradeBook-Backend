from config.extensions import db
from models.user_model import User
from mongoengine import CASCADE

class Trade(db.Document):
    user = db.ReferenceField(User, reverse_delete_rule=CASCADE)
    script = db.StringField()
    entries = db.ListField() # (date, qty, price)
    exits = db.ListField()
    total_qty = db.IntField()
    notes = db.ListField()
    chart_url = db.URLField()
    status = db.StringField()

    def to_json(self):
        return {
            "user": self.user.email,
            "script": self.script,
            "entries" : self.entries,
            "exits": self.exits,
            "notes" : self.notes,
            "chart_url": self.chart_url,
            "status": self.status,
            "total_qty" : self.total_qty
        }
