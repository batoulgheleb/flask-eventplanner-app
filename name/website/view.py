#this is a file to store all the routes of the webpage 
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file 
from barcode import Code39
from barcode.writer import SVGWriter
import random
from datetime import datetime
from flask_mail import Mail, Message  

from itsdangerous import URLSafeTimedSerializer, SignatureExpired
s = URLSafeTimedSerializer("giginator")

#import Databases to use 
from . import db, mail
from .models import User, Event
from io import BytesIO


#for login, rendering the homepage so only some elements show 
#used to access information about the currently logged in user 
from flask_login import login_user, login_required, logout_user, current_user 

#password hashing (one way function with no inverse)
from werkzeug.security import generate_password_hash, check_password_hash

views = Blueprint("views", __name__)


@views.route("/Register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        
        user = request.form.get("name")
        email = request.form.get("email")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")
        

        exsisting_user = User.query.filter_by(email=email).first()
        
        if exsisting_user:
            flash("Account with this Email already exists", category="error")
            return redirect(url_for("views.login"))
            
        if len(email) < 1:
            flash("Email is required to Register", category="error")
        elif password1 != password2:
            flash("Passwords do not match", category="error")
        elif len(password1) < 8:
            flash("Password must be at least 8 characters", category="error")
        else:
            #adding the user to the data-base when they first register 
            new_user = User(name=user, email=email, password=generate_password_hash(password1, "sha256"), admin=False, organiser=False, is_verified=False)
            db.session.add(new_user)
            db.session.commit()
            
            if new_user.is_verified:
                login_user(new_user, remember=True)
                flash("Account Created Successfully", category="success")
            else:
                flash("Registration successful, you can now login", category="success")
                token = s.dumps(email, salt='email-confirm')
                msg = Message('Confirm Email', sender='ghelebatoul@gmail.com', recipients=[email])
                link = url_for('views.confirm_email', token=token, _external=True)
                msg.body = 'Your link is {}'.format(link)
                mail.send(msg)
                new_user.is_verified = True

                return render_template("redirect.html")
            
            return redirect(url_for("views.register"))
     
    return render_template("register.html", user=current_user)
    
@views.route('/confirm_email/<token>')
def confirm_email(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
    except SignatureExpired:
        return '<h1>The token is expired!</h1>'
    
    return redirect(url_for("views.user"))

    
@views.route("/login", methods=["POST", "GET"])
def login():
    events = Event.query.all()
    if request.method == "POST":
        
        email = request.form.get("email")
        password = request.form.get("password")
        
        if len(email) < 1:
            flash("Email is required for login", category="error")
        elif len(password) < 1:
            flash("Please enter a password to login", category="error")
        else:
            user = User.query.filter_by(email=email).first()
            if user:
                if check_password_hash(user.password, password):
                    login_user(User.query.filter_by(email=email).first(), remember=True)
                    flash("Logged in successfully", category="sucess")
                else:
                    flash("Incorrect password, Please try again", category="error")
                    return redirect(url_for("views.login"))
                    
                return redirect(url_for("views.user"))
            else:
                flash("Account Under this email account does not exist", category="error")
                return redirect(url_for("views.register"))
    else:
        user = current_user 
        if user.is_authenticated:
            return redirect(url_for("views.user"))
         
    return render_template("login.html", user=current_user, events=events)

@views.route("/", methods=["POST", "GET"])
@login_required 
def user():
    events = Event.query.all()
        
    return render_template("user.html", user=current_user, events=events)
  
    
@views.route("/logout")  
@login_required
def logout():
    logout_user()
    flash("Logged out successfully", category="success")
    
    return redirect(url_for("views.login"))


@views.route("/Register_as_Admin", methods=["POST", "GET"])
@login_required
def admin_register():
    if request.method == "POST":
        code = request.form.get("code")
        user = current_user
        if code == "Dc5_G1gz":
            flash("Registered as Administrator", category="success")
            user.admin = True
            db.session.commit()
            return redirect(url_for("views.user"))
        else:
            flash("Incorrect code entered", category="error")
        
    return render_template("admin_register.html", user=current_user)


@views.route("/myEvents", methods=["GET", "POST"])
@login_required
def my_events():
    
    #adding an event to the user 
    if request.method == "POST":
        name = request.form.get("name")
        event = request.form.get("event") 
        time = request.form.get("time")
        date = request.form.get("date")
        location = request.form.get("location")
        capacity = request.form.get("capacity")     
        duration = request.form.get("duration")
        image = request.form.get("image")
        
        date_time = date + " " + time 
        datetime_obj = datetime.strptime(date_time, '%Y-%m-%d %H:%M')
        
        if len(event) < 1:
            flash("Too little information", category="error")
        else:
            new_event = Event(data=event, name=name, date=datetime_obj, location=location, capacity=capacity, admin_id=current_user.id, duration=duration, image=image)
            db.session.add(new_event)
            db.session.commit()
            flash("New Event added successfully", category="success") 
            
    return render_template("myEvents.html", user=current_user)

@views.route('/delete-event/<event_id>')
def delete_event(event_id):
    
    user = current_user
    event = Event.query.filter_by(id=event_id).first()
    if event:
        #select the event from the database and delete 
        db.session.delete(event)
        db.session.commit()
        
        #delete event and therefore notify the attendees of that event cancellation 
        if event.attendee_events:
            for attendee in event.attendee_events:
                message = Message('Cancelled Event', sender='ghelebatoul@gmail.com', recipients=[attendee.email])
                message.body = 'We regret to inform you that your event will no longer be taking place; we apologise to any inconvience this causes'
                mail.send(message)
            flash("Event deleted successfully, and attendees have been notified", category="success")
        else:
            flash("Event deleted successfully", category="success")
    else:
        flash("Error occurred; event cannot be deleted", category="error")
    
    return redirect(url_for("views.my_events"))

@views.route("/book", methods=["GET", "POST"])
@login_required
def book():
    events = Event.query.all()
  
    return render_template("book.html", user=current_user, events=events)

@views.route("/book_event/<event_id>")
def book_event(event_id):
    
    user = current_user
    event = Event.query.filter_by(id=event_id).first()
    
    if event:
        if event.capacity == 0:
            flash("Event is fully booked!", category="error")
            return redirect(url_for("views.book"))
        
        user.attendee_event.append(event)
        event.capacity = event.capacity - 1
        db.session.commit()
        flash("Booked event successfully", category="success")  
    
    return redirect(url_for("views.book"))
        


@views.route("/my_tickets")
@login_required
def tickets():
    
    ticket_list = current_user.attendee_event 
    
    return render_template("tickets.html", user=current_user, ticket_list=ticket_list)


@views.route('/barcode/<barcode_value>')
def generate_barcode(barcode_value):
   
    random_number = random.randint(100000000, 999999999)
    unique_barcode = str(barcode_value) + str(current_user.id) + str(random_number)
    barcode = Code39(unique_barcode, writer=SVGWriter())
    
    barcode_bytes = BytesIO()
    barcode.write(barcode_bytes)
    barcode_bytes.seek(0)

    return send_file(barcode_bytes, mimetype='image/svg+xml')

@views.route('/delete-ticket/<ticket_id>')
def delete_ticket(ticket_id):
    
    user = current_user
    event = Event.query.filter_by(id=ticket_id).first()
    if event:
        user.attendee_event.remove(event)
        event.capacity = event.capacity + 1
        db.session.commit()
        flash("Ticket deleted successfully", category="success")
    else:
        flash("Error occurred, ticket cannot be deleted", category="error")
    
    return redirect(url_for("views.tickets"))

@views.route("/manage_attendees", methods=["GET", "POST"])
@login_required
def manage_attendees():
    #access the events that that admin created then list the attendees for each of the events and emails 
    admin_id = current_user.id
    events = Event.query.filter_by(admin_id=admin_id).all()                
        
    return render_template("manage_attendees.html", user=current_user, events=events)

@views.route('/promote/<attendee_id>')
def promote(attendee_id):
    
    admin_id = current_user.id 
    from_database = User.query.filter_by(id=attendee_id).first()
    if from_database:
        from_database.organiser = True 
        db.session.commit()
        flash("Organisor added successfully", category="success")
    else: 
        flash("error occurred, and organisor is not added", category="error")
    
    return redirect(url_for("views.manage_attendees"))

@views.route("/organisor", methods=["GET", "POST"])
@login_required
def organisor():
    #the organisor has access to the events they have been appointed organisor for
    events = Event.query.all()
    
    #adding an event to the user 
    if request.method == "POST":
        name = request.form.get("name")
        event = request.form.get("event") 
        time = request.form.get("time")
        date = request.form.get("date")
        location = request.form.get("location")
        capacity = request.form.get("capacity")     
        duration = request.form.get("duration")
        
        image = request.form.get("image")
      
        
        date_time = date + " " + time 
        datetime_obj = datetime.strptime(date_time, '%Y-%m-%d %H:%M')
        
        if len(event) < 1:
            flash("Too little information", category="error")
        else:
            user = current_user
            new_event = Event(data=event, name=name, date=datetime_obj, location=location, capacity=capacity, admin_id=current_user.id, duration=duration, image=image)
            db.session.add(new_event)
            user.attendee_event.append(new_event)
            new_event.capacity = int(new_event.capacity) - 1
            db.session.commit()
            flash("New Event added successfully, and ticket booked!", category="success")  
            
    return render_template("organisor.html",  user=current_user, events=events)

@views.route('/delete_organisor_event/<event_id>')
def delete_organisor_event(event_id):
    
    event = Event.query.filter_by(id=event_id).first()
    if event:
        #select the event from the database and delete 
        db.session.delete(event)
        db.session.commit()
        flash("Event deleted successfully", category="success")
    else:
        flash("Error occurred; event cannot be deleted", category="error")
    
    return redirect(url_for("views.organisor"))