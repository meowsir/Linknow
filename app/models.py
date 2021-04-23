from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login
from flask_login import UserMixin
from hashlib import md5

class Schedule(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    meeting_roomid = db.Column(db.String(32), db.ForeignKey('meeting.roomid'), primary_key=True)
    state = db.Column(db.String(20))
    # state: [Wait, Accept]
    meeting = db.relationship('Meeting', back_populates='users')
    user = db.relationship('User', back_populates='meetings')

    def __repr__(self):
        return '<Schedule {}>'.format(str(self.user_id)+" "+str(self.meeting_roomid)+" "+self.state)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(64), index=True, unique=True)
    telephone = db.Column(db.String(11), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    hosts = db.relationship('Meeting', backref='is_sponsor', lazy='dynamic')
    meetings = db.relationship('Schedule', back_populates='user')

    def __repr__(self):
        return '<User {}>'.format(self.telephone+" "+self.nickname)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://sdn.geekzu.org/avatar/{}?d=retro&s={}'.format(digest, size)

    def accept(self, meeting):
        if not self.is_attending(meeting):
            self.which_meetings.append(meeting)
    
    def refuse(self, meeting):
        if self.is_attending(meeting):
            self.which_meetings.remove(meeting)

    def is_attending(self, meeting):
        return self.which_meetings.filter(Schedule.meeting_id == meeting.id).count() > 0

    def my_schedule_meetings(self):
        return Meeting.query.join(Schedule).filter(Schedule.user_id == self.id, Schedule.state == 'Wait').order_by(Meeting.start_time.desc()).all()
    
    def my_accept_meetings(self):
        return Meeting.query.join(Schedule).filter(Schedule.user_id == self.id, Schedule.state == 'Accept').order_by(Meeting.start_time.desc()).all()

class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sponsor = db.Column(db.Integer, db.ForeignKey('user.id'))
    roomid = db.Column(db.String(32), index=True, unique=True)
    qrcode = db.Column(db.String(120), index=True, unique=True)
    users = db.relationship('Schedule', back_populates='meeting')
    introduction = db.Column(db.String(120))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    # state: [Coming, Present, End]
    state = db.Column(db.String(20))
    def __repr__(self):
        return '<Meeting {}>'.format(self.roomid)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))