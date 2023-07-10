from website import db 
from flask_login import UserMixin

#relationship between attendees/organisers and events 
association = db.Table('association',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),    
    db.Column('event_id', db.Integer, db.ForeignKey('event.id'))    
)

#for users inherit from UserMixin 
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    
    #to verify email 
    is_verified = db.Column(db.Boolean(), default=False, unique=False)
    
    #attendees can be promoted to organiser to events until the event is deleted 
    admin = db.Column(db.Boolean(), default=False, unique=False)
    organiser = db.Column(db.Boolean(), default=False, unique=False)
    
    #every time event is created by admin, event is added or user buys ticket for
    events = db.relationship('Event') #list of all events for admin
    
    #events for the attendees or the Organisers 
    attendee_event = db.relationship('Event', secondary=association, backref='attendee_events', lazy='select')
    


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    #all events must link to the Admin
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    #add attributes asscoiated with each event 
    name = db.Column(db.String(100))
    data = db.Column(db.String(1000))
    date = db.Column(db.DateTime(), nullable=False)
    capacity = db.Column(db.Integer)
    location = db.Column(db.String(100))
    #time duration in mins calcuated and formated in routes code 
    duration = db.Column(db.Integer)
    
    #adding an image to each event 
    image = db.Column(db.String(1000), nullable=True)

