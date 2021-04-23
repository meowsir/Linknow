from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, DateField, DateTimeField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app.models import User
from datetime import datetime, timedelta, timezone

class LoginForm(FlaskForm):
    telephone = StringField('Telephone', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    telephone = StringField('Telephone', validators=[DataRequired()])
    nickname = StringField('Nickname', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_telephone(self, telephone):
        user = User.query.filter_by(telephone=telephone.data).first()
        if user is not None:
            raise ValidationError('Sorry, Tele number has beens registed before.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Sorry, email has beens registed before.')

class StartForm(FlaskForm):
    roomid = StringField('Room number', validators=[DataRequired()])
    nickname = StringField('Your nickname', validators=[DataRequired()])
    submit = SubmitField('Start')

class ScheduleForm(FlaskForm):
    roomid = StringField('Room number', validators=[DataRequired()])
    introduction = StringField('Meeting introduction', validators=[DataRequired()])
    start_time = StringField('Start time', id='stimepicker', default = datetime.now(), validators=[DataRequired()])
    end_time = StringField('End time', id='etimepicker', default = datetime.now()+timedelta(hours=1), validators=[DataRequired()])
    submit = SubmitField('Confirm')