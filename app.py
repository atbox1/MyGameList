from enum import unique
from flask import Flask, render_template, redirect, url_for, g, request, session, abort, flash
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, BooleanField, FileField
from wtforms.validators import InputRequired, Email, Length
from flask_sqlalchemy  import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from datetime import datetime
from flask_uploads import configure_uploads, IMAGES, UploadSet
#from sqlalchemy import func

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Thisisweresecret!!!!'
app.config['SECRET_KEY'] = 'thisisscret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://///mnt/c/Users/Ali/Documents/School/2021/Digital Solutions/Term 2/Assessment/Code/MyGamelist/user_account.db'
app.config['FLASK_ADMIN_SWATCH'] = 'cosmo'
app.config['UPLOADED_PHOTOS_DEST'] = 'images'

photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)
bootstrap = Bootstrap(app)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
admin = Admin(app, name = 'MyGameList Admin', template_mode= 'bootstrap3' )

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(160))
    profile_image = db.Column(db.String(140))

    def __init__(self, username, email, profile_image, password):
 
        self.username = username
        self.email = email
        self.profile_image = profile_image
        self.password = password
 
class Games(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25), unique=True)
    developer = db.Column(db.String(50), unique=True)
    description = db.Column(db.String(240))
    realease_date = db.Column(db.DateTime)
    platforms = db.Column(db.String(40))
    img = db.Column(db.String(100))

class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=160)])
    remember = BooleanField('remember me')

class RegisterForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=160)])
    profile_image = FileField('Insert profile image', validators=[InputRequired()])

class AddGame(FlaskForm):
    name = StringField('Game Name')
    developer = StringField('Developer', validators=[InputRequired()])
    description = StringField('Game Description', validators=[InputRequired()])
    platforms = StringField('Platforms', validators=[InputRequired()])
    img = FileField('Image', validators=[InputRequired()])

class MyModelView(ModelView):
    def is_accessible(self):
        return  current_user.is_authenticated 

class SecureModelView(ModelView):
    def is_accessible(self):
        if "logged_in" in session:
            return True
        else:
            abort(403)
    #def get_query(self):
        info = User()
        return self.session.query(self.model).filter('alkigi'==current_user.username)

    #def get_count_query(self):
        info = User()
        return self.session.query(func.count('*')).filter('alkigi'==current_user.username)

admin.add_view(SecureModelView(User, db.session))
admin.add_view(SecureModelView(Games, db.session))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                #session["logged_in"] = True
                return redirect('/account_profile')

        return '<h1>Invalid username or password</h1>'

    return render_template('login.html', form=form)


@app.route("/admin_login", methods=["GET", "POST"])
def login_admin():
    if request.method == "POST":
        if request.form.get("username") == "admin" and request.form.get("password") == "password":
            session['logged_in'] = True
            return redirect("/admin")
        else:
            return render_template("admin_login.html", failed=True)
    return render_template("admin_login.html")




@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        image = photos.url(photos.save(form.profile_image.data))
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password, profile_image = image)
        db.session.add(new_user)
        db.session.commit() 
        flash("User Account Successfully Registered")
        return redirect(url_for('login'))
        

    return render_template('signup.html', form=form)


@app.route('/account_profile')
@login_required
def profile_page():
    return render_template('account_profile.html', name = current_user.username, email = current_user.email, img = current_user.profile_image)

@app.route('/add_game_page', methods=['GET', 'POST'])

def Add_Game():
    form = AddGame()
    if form.validate_on_submit():
        img = photos.url(photos.save(form.img.data))
        new_game = Games(name=form.name.data, developer=form.developer.data, description=form.description.data, platforms = form.platforms.data, img = img)
        db.session.add(new_game)
        db.session.commit()

        return redirect(url_for('games'))
    return render_template('Add_Game.html', form = form)
@app.route('/games')
def games():
    games = Games.query.all()
    return render_template('games_page.html', games = games)
    
@app.route('/game/<id>')
def game(id):
    game = Games.query.filter_by(id=id).first()

    return render_template('view-game.html', game=game)

@login_required
def logout():
    session.clear()
    logout_user()
    return redirect(url_for('index'))

@app.route('/account_profile/edit')
def User_edit():
    all_data = User.query.all()

    return render_template("user_profile-edit.html", employees = all_data)

@app.route('/update', methods = ['GET', 'POST'])
def update():

    if request.method == 'POST':
        my_data = User.query.get(request.form.get('id'))

        my_data.username = request.form['name']
        my_data.email = request.form['email']
        my_data.profile_image = request.form['phone']

        db.session.commit()
        flash("User Account Updated Successfully")

        return redirect(url_for('User_edit'))

@app.route('/delete/<id>/', methods = ['GET', 'POST'])
def delete(id):
    my_data = User.query.get(id)
    db.session.delete(my_data)
    db.session.commit()
    flash("User Deleted Successfully")

    return redirect(url_for('User_edit'))

if __name__ == '__main__':
    app.run(debug=True)




