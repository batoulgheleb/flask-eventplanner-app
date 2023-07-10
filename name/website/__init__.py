from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_mail import Mail
from flask_login import LoginManager 

#define a new database object that is used to manage the database 
db = SQLAlchemy()
DB_NAME = "database.db"

#defining the mail constructor 
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = "123"
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    #configuring mail for verfication and notifications 
    app.config['DEBUG'] = True
    app.config['MAIL_SUPPRESS_SEND'] = False
    mail.init_app(app)
    
    #register blueprints 
    from .view import views 
    app.register_blueprint(views, url_prefix="/")
    
    #create data base from models script after checking one doesnt exist 
    from .models import User, Event 
    with app.app_context():
        db.drop_all()
        db.create_all()
        
    #create login manager object 
    login_manager = LoginManager()
    login_manager.login_view = "views.login"
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
       
    return app

