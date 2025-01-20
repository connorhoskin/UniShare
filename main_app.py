import requests as requests
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import boto3
app = Flask(__name__)
# helllooo
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
s3 = boto3.client('s3', region_name='us-east-1')
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:adminadmin@database-1.c0h8oostj5lp.us-east-1.rds.amazonaws.com/myappdb'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'some_secret_key'

db = SQLAlchemy(app)
migrate = Migrate(app, db)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


user_studygroup = db.Table('user_studygroup',
                           db.Column('user_id', db.Integer, db.ForeignKey('User.id'), primary_key=True),
                           db.Column('studygroup_id', db.Integer, db.ForeignKey('StudyGroup.id'), primary_key=True)
                           )


# User Model
class User(db.Model, UserMixin):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    studygroups = db.relationship('StudyGroup', secondary='user_studygroup', back_populates='members')


class StudyGroup(db.Model):
    __tablename__ = 'StudyGroup'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

    members = db.relationship('User', secondary='user_studygroup', back_populates='studygroups')

class Group(db.Model):
    __tablename__ = 'groups'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)

    files = db.relationship('File', back_populates='group')

class File(db.Model):
    __tablename__ = 'files'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'))
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.Text, nullable=False)

    group = db.relationship('Group', back_populates='files')


@app.route('/')
def index():
    return render_template('login.html')


def get_user_groups(user_id):

    user = User.query.get(user_id)
    if user:
        return user.studygroups
    return []
    
@app.route('/view_files/<group_id>', methods=['GET'])  # Add group_id to the route
@login_required
def view_files(group_id):
    # List files in S3 under the specific group prefix
    response = s3.list_objects_v2(Bucket='unishare-media', Prefix=f"{group_id}/")

    files = []
    if 'Contents' in response:
        for obj in response['Contents']:
            files.append({
                "filename": obj['Key'].split('/')[-1],  # The actual file name after the last '/'
                "filepath": f"https://unishare-media.s3.amazonaws.com/{obj['Key']}"  # Direct link to the file
            })

    return render_template('view_files.html', files=files)



@app.route('/upload_to_s3', methods=['POST'])
@login_required
def upload_to_s3():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file:
        group_id = request.form.get("group_id")
        if not group_id:
            flash('Study group missing')
            return redirect(request.url)
        # Create a unique file path for the study group
        file_path = f"{group_id}/{file.filename}"
        s3.upload_fileobj(file, 'unishare-media', file_path)
        flash('File successfully uploaded')
        return redirect(url_for('dashboard'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        user_by_username = User.query.filter_by(username=username).first()
        user_by_email = User.query.filter_by(email=email).first()

        if user_by_username:
            error = "Username already exists."
        elif user_by_email:
            error = "Email already registered."
        else:
            new_user = User(username=username, email=email, password=password)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))

    return render_template('register.html', error=error)


@app.route('/view_studygroups')
@login_required
def view_studygroups():
    studygroups = StudyGroup.query.all()
    return render_template('view_studygroups.html', studygroups=studygroups)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            error = "Username or password is incorrect"

    return render_template('login.html', error=error)


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


@app.route('/create_group', methods=['POST'])
@login_required
def create_group():
    group_name = request.form['group_name']
    group = StudyGroup.query.filter_by(name=group_name).first()
    if group:
        flash('A group with that name already exists!', 'error')
        return redirect(url_for('dashboard'))
    else:
        new_group = StudyGroup(name=group_name)
        new_group.members.append(current_user)  # Use new_group here
        db.session.add(new_group)
        db.session.commit()
        return redirect(url_for('dashboard'))


@app.route('/join_group', methods=['POST'])
@login_required
def join_group():
    group_name = request.form['group_name']
    group = StudyGroup.query.filter_by(name=group_name).first()
    if group:
        if current_user in group.members:
            flash('You are already a member of this group!', 'error')
            return redirect(url_for('dashboard'))
        else:
            group.members.append(current_user)
            db.session.commit()
            return redirect(url_for('dashboard'))
    else:
        flash('Group not found!', 'error')
        return redirect(url_for('dashboard'))


@app.route('/leave_group', methods=['POST'])
@login_required
def leave_group():
    group_name = request.form['group_name']
    group = StudyGroup.query.filter_by(name=group_name).first()
    if group:
        if current_user not in group.members:
            flash('You are not a member of this group!', 'error')
            return redirect(url_for('dashboard'))
        else:
            group.members.remove(current_user)
            db.session.commit()
            return redirect(url_for('dashboard'))
    else:
        flash('Group not found!', 'error')
        return redirect(url_for('dashboard'))


@app.route('/session/<group_id>')
def session(group_id):
    return render_template('session.html', group_id=group_id)





@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))





if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001)
