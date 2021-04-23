from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from app import *
from app.forms import *
from app.models import User, Meeting, Schedule
from werkzeug.urls import url_parse
from datetime import datetime, timedelta, timezone

host = "192.168.108.133"
hotdot = "192.168.73.251"

@app.route('/schedule', methods=['GET', 'POST'])
@login_required
def schedule():
    form = ScheduleForm()
    form.introduction.data = current_user.nickname+"'s fast meeting"
    if form.validate_on_submit():
        st = datetime.strptime(form.start_time.data.split(' ')[0]+' '+form.start_time.data.split(' ')[1], "%Y-%m-%d %H:%M")-timedelta(hours=8)
        et = datetime.strptime(form.end_time.data.split(' ')[0]+' '+form.end_time.data.split(' ')[1], "%Y-%m-%d %H:%M")-timedelta(hours=8)
        m = Meeting(sponsor=current_user.id, roomid=form.roomid.data, 
        introduction=form.introduction.data, start_time=st, end_time=et)
        s = Schedule(user_id=current_user.id, meeting_roomid=m.roomid, state="Accept")
        db.session.add(m)
        db.session.add(s)
        db.session.commit()
        flash('Schedule success ^_^')
        return redirect(url_for('myPage'))
    return render_template("schedule.html", title='Schedule', form=form, user=current_user)    

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(telephone=form.telephone.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid telephone or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        flash('Login success')
        return redirect(next_page)
    return render_template('login.html', title='Log In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(telephone=form.telephone.data, nickname=form.nickname.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/myPage', methods=['GET', 'POST'])
@login_required
def myPage():
    schedule_meetings = current_user.my_schedule_meetings()
    accept_meetings = current_user.my_accept_meetings()
    for sm in schedule_meetings:
        if datetime.utcnow() > sm.start_time - timedelta(minutes=30):
            sm.state = "Present"
        if datetime.utcnow() - sm.end_time > timedelta(hours=1):
            sm.state = "End"
        if datetime.utcnow() < sm.start_time - timedelta(minutes=30):
            sm.state = "Coming"
    for am in accept_meetings:
        if datetime.utcnow() > am.start_time - timedelta(minutes=30):
            am.state = "Present"
        if datetime.utcnow() - am.end_time > timedelta(hours=1):
            am.state = "End"
        if datetime.utcnow() < am.start_time - timedelta(minutes=30):
            am.state = "Coming"
    db.session.commit()
    users = User.query.all()
    emailmap = {}
    telemap = {}
    for eachuser in users:
        emailmap[eachuser.id] = eachuser.email
        telemap[eachuser.id] = eachuser.telephone
    if request.method == "POST":
        email = request.form['emailgetter']
        meeting_roomid = request.form['roomidform']
        user = User.query.filter_by(email=email).first()
        try:
            if user:
                s = Schedule(user_id=user.id, meeting_roomid=meeting_roomid, state="Wait")
                db.session.add(s)
                db.session.commit()
                flash('Invite success')
                return redirect(url_for('myPage'))
            else:
                flash('No such user.Invite failed!')
                return redirect(url_for('myPage'))
        except Exception as e:
            flash('Invite failed!')
            return redirect(url_for('myPage'))
    return render_template('user.html', user=current_user, schedule_meetings=schedule_meetings,
    accept_meetings=accept_meetings, title='me', emailmap=emailmap, telemap=telemap)

@app.route('/accept/<uid>/<mid>', methods=['GET', 'POST'])
@login_required
def accept(uid, mid):
    schedule = Schedule.query.filter_by(user_id=uid, meeting_roomid=mid).first()
    schedule.state="Accept"
    db.session.commit()
    flash("Accept success")
    return redirect(url_for('myPage'))

@app.route('/refuse/<uid>/<mid>', methods=['GET', 'POST'])
@login_required
def refuse(uid, mid):
    schedule = Schedule.query.filter_by(user_id=uid, meeting_roomid=mid).first()
    db.session.delete(schedule)
    db.session.commit()
    flash("Refuse success")
    return redirect(url_for('myPage'))

@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = StartForm(nickname=current_user.nickname)
    if form.validate_on_submit():
        u = current_user
        u.nickname = form.nickname.data
        db.session.commit()
        return redirect(url_for("entry_checkpoint", room_id=form.roomid.data, display_name=form.nickname.data))
    return render_template("index.html", title='Home Page', form=form, user=current_user)

# webrtc
@app.route("/room/<string:room_id>/", methods=["GET", "POST"])
@login_required
def enter_room(room_id):
    if room_id not in session:
        return redirect(url_for("entry_checkpoint", room_id=room_id, display_name=current_user.nickname))
    return render_template("chatroom.html", title='room['+room_id+']', user=current_user, room_id=room_id, display_name=session[room_id]["name"], mute_audio=session[room_id]["mute_audio"], mute_video=session[room_id]["mute_video"])

@app.route("/room/<string:room_id>/checkpoint/<string:display_name>", methods=["GET", "POST"])
@login_required
def entry_checkpoint(room_id, display_name):
    if request.method == "POST":
        mute_audio = request.form['mute_audio']
        mute_video = request.form['mute_video']
        session[room_id] = {"name": display_name, "mute_audio":mute_audio, "mute_video":mute_video}
        return redirect(url_for("enter_room", room_id=room_id))
    return render_template("chatroom_checkpoint.html", title='checkpoint['+room_id+']', room_id=room_id, user=current_user)