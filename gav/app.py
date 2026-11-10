from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import uuid
import random
import string
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hardahi_village_secret_key_12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hardahi.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_IMAGE_EXT = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_VIDEO_EXT = {'mp4', 'webm', 'ogg', 'mov'}

os.makedirs(os.path.join(UPLOAD_FOLDER, 'photos'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'reels'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'complaints'), exist_ok=True)

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    guardian = db.Column(db.String(100))
    phone = db.Column(db.String(15), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    village = db.Column(db.String(100), default="Hardahi")
    ward = db.Column(db.String(50))
    occupation = db.Column(db.String(100))
    photo = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Reel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), default="Village Reel")
    video_filename = db.Column(db.String(200), nullable=False)
    uploader_name = db.Column(db.String(100), default="Gramvasi")
    uploader_account = db.Column(db.String(50), default="Hardahi Resident")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_name = db.Column(db.String(100), default="Gramvasi")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    message = db.Column(db.Text, nullable=False)
    video_filename = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

def allowed_file(filename, allowed_set):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_set

def generate_custom_id():
    letters = ''.join(random.choices(string.ascii_uppercase, k=4))
    digits = ''.join(random.choices(string.digits, k=4))
    return f"{letters}-{digits}"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/gallery')
def gallery():
    return render_template('gallery.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        guardian = request.form.get('guardian')
        phone = request.form.get('phone')
        password = request.form.get('password')
        ward = request.form.get('ward')
        occupation = request.form.get('occupation')
        
        if User.query.filter_by(phone=phone).first():
            flash('यह मोबाइल नंबर पहले से रजिस्टर्ड है।', 'danger')
            return redirect(url_for('signup'))

        photo_filename = None
        file = request.files.get('photo')
        if file and allowed_file(file.filename, ALLOWED_IMAGE_EXT):
            ext = file.filename.rsplit('.', 1)[1].lower()
            photo_filename = f"photos/{uuid.uuid4().hex}.{ext}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))

        member_id = generate_custom_id()
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        
        new_user = User(
            member_id=member_id,
            name=name,
            guardian=guardian,
            phone=phone,
            password=hashed_pw,
            ward=ward,
            occupation=occupation,
            photo=photo_filename
        )
        db.session.add(new_user)
        db.session.commit()

        session['user_id'] = new_user.id
        session['user_name'] = new_user.name
        session['member_id'] = new_user.member_id
        flash('रजिस्ट्रेशन सफल रहा! आपका ID Card तैयार है।', 'success')
        return redirect(url_for('id_card'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')
        
        user = User.query.filter_by(phone=phone).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['member_id'] = user.member_id
            flash('लॉगिन सफल!', 'success')
            return redirect(url_for('profile'))
        else:
            flash('गलत मोबाइल नंबर या पासवर्ड।', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('member_id', None)
    flash('आप लॉगआउट हो चुके हैं।', 'info')
    return redirect(url_for('home'))

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user)

@app.route('/id-card')
def id_card():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    return render_template('id_card.html', user=user)

@app.route('/reels')
def reels():
    all_reels = Reel.query.order_by(Reel.created_at.desc()).all()
    return render_template('reels.html', reels=all_reels)

@app.route('/upload-reel', methods=['POST'])
def upload_reel():
    file = request.files.get('video')
    if file and allowed_file(file.filename, ALLOWED_VIDEO_EXT):
        ext = file.filename.rsplit('.', 1)[1].lower()
        video_filename = f"reels/{uuid.uuid4().hex}.{ext}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], video_filename))
        
        uploader_n = session.get('user_name', 'Hardahi Resident')
        uploader_acc = f"ID: {session.get('member_id', 'HRDH-USER')}"
        
        new_reel = Reel(
            title="Gram Reel",
            video_filename=video_filename,
            uploader_name=uploader_n,
            uploader_account=uploader_acc
        )
        db.session.add(new_reel)
        db.session.commit()
        flash('Reel सफलतापूर्वक अपलोड हो गई!', 'success')
    else:
        flash('कृपया एक वैध वीडियो (MP4) चुनें।', 'danger')
    return redirect(url_for('reels'))

@app.route('/news', methods=['GET', 'POST'])
def news():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        author = session.get('user_name', 'Hardahi Resident')
        
        if title and content:
            new_item = News(title=title, content=content, author_name=author)
            db.session.add(new_item)
            db.session.commit()
            flash('समाचार सफलतापूर्वक पोस्ट हो गया!', 'success')
            return redirect(url_for('news'))
            
    all_news = News.query.order_by(News.created_at.desc()).all()
    return render_template('news.html', news_list=all_news)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        message = request.form.get('message')
        
        video_filename = None
        file = request.files.get('video')
        if file and allowed_file(file.filename, ALLOWED_VIDEO_EXT):
            ext = file.filename.rsplit('.', 1)[1].lower()
            video_filename = f"complaints/{uuid.uuid4().hex}.{ext}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], video_filename))

        new_complaint = Complaint(
            name=name,
            phone=phone,
            message=message,
            video_filename=video_filename,
            created_at=datetime.now()
        )
        db.session.add(new_complaint)
        db.session.commit()
        flash('आपकी शिकायत दर्ज कर ली गई है!', 'success')
        return redirect(url_for('contact'))
        
    all_complaints = Complaint.query.order_by(Complaint.created_at.desc()).all()
    return render_template('contact.html', complaints=all_complaints)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(port=5000,host="192.168.197.214",debug=True)
