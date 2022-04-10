from config.extensions import db
import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Document):

    #! if you set any field as primary key then that field will be saved as "_id" in database. You have to fetch it in same way
    first_name = db.StringField(required = True)
    last_name = db.StringField()
    email = db.StringField()
    phone = db.StringField(required = True)
    password_hash = db.StringField(required = True)
    created_at = db.DateTimeField(default=datetime.datetime.now())

    def set_password(self, password):
        password_hash = generate_password_hash(password)
        self.password_hash = password_hash
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_json(self):
        return {
            "name": f"{self.first_name} {self.last_name}",
            "email": self.email,
            "phone": self.phone
        }