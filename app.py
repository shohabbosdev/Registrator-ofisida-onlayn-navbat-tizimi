import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_babel import Babel, _
from datetime import datetime, timedelta
import pytz
import csv
from io import StringIO
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import mimetypes
import logging

# Logging sozlash
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Loyiha katalogini aniqlashtirish
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(BASE_DIR, "queue.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key_for_development')
app.config['BABEL_DEFAULT_LOCALE'] = 'uz'
app.config['BABEL_DEFAULT_TIMEZONE'] = 'Asia/Tashkent'
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static/uploads')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['ALLOWED_MIME_TYPES'] = {'image/png', 'image/jpeg', 'image/gif'}
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB cheklov
db = SQLAlchemy(app)
babel = Babel(app)

# Upload papkasini yaratish
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Fayl kengaytmasi va MIME turini tekshirish
def allowed_file(filename, file_stream):
    mime_type, _ = mimetypes.guess_type(filename)
    return (
        '.' in filename and
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS'] and
        mime_type in app.config['ALLOWED_MIME_TYPES']
    )

# Foydalanuvchi tili sessiondan olinadi
def get_locale():
    return session.get('language', 'uz')

# Flask-Babel sozlamasi
babel.init_app(app, locale_selector=get_locale)

# Ma'lumotlar bazasi modellari
class ServiceType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Queue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    queue_number = db.Column(db.Integer, nullable=False)
    prefix = db.Column(db.String(1), nullable=False)
    service_type_id = db.Column(db.Integer, db.ForeignKey('service_type.id'), nullable=False)
    service_type = db.relationship('ServiceType', backref=db.backref('queues', lazy=True))
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(pytz.timezone('Asia/Tashkent')))
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending holat qo‘shildi
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    group = db.Column(db.String(20))
    employee = db.Column(db.String(50))

    @property
    def formatted_queue_number(self):
        return f"{self.prefix}{self.queue_number:03d}"

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)  # Xeshlangan parol
    role = db.Column(db.String(20), nullable=False)
    profile_picture = db.Column(db.String(100), nullable=True)

# Ma'lumotlar bazasini yaratish
with app.app_context():
    logger.debug("Ma'lumotlar bazasini yaratish boshlandi...")
    try:
        db.create_all()
        logger.debug("Ma'lumotlar bazasi muvaffaqiyatli yaratildi!")
        if not ServiceType.query.first():
            logger.debug("Xizmat turlari va foydalanuvchilar qo'shilmoqda...")
            services = [
                ServiceType(name='QR kodli diplom'),
                ServiceType(name='Akademik ma\'lumotnoma va transkript olish'),
                ServiceType(name='Kredit-modul tizimi va qayta o\'qishni tashkil etish'),
                ServiceType(name='Akademik mobillik'),
                ServiceType(name='Imtihon ro\'yxati'),
                ServiceType(name='GPA ma\'lumotnoma'),
                ServiceType(name='Shaxsiy grafik'),
                ServiceType(name='HEMIS platformasidan kursga o\'tkazish'),
                ServiceType(name='Parolni tiklash'),
                ServiceType(name='Guruhdan guruhga o\'tkazish'),
                ServiceType(name='Stipendiya haqida ma\'lumot'),
                ServiceType(name='O\'qishga qabul va ko\'chirish bo\'yicha konsultatsiya'),
                ServiceType(name='Hisob varaqasini shakllantirish'),
                ServiceType(name='Talabalarning yotoqxonalarga joylashish shartnomasi va yo\'llanma berish'),
                ServiceType(name='Ijara subsidiyasi uchun ariza yozishga ko\'maklashish'),
                ServiceType(name='To\'lov-shartnoma summasi haqida ma\'lumot'),
                ServiceType(name='Boshqa xizmatlar')
            ]
            for service in services:
                db.session.add(service)
            admin = User(username='root', password=generate_password_hash('Shoh@1994'), role='admin')
            table1 = User(username='table1', password=generate_password_hash('table1'), role='employee')
            table2 = User(username='table2', password=generate_password_hash('table2'), role='employee')
            table3 = User(username='table3', password=generate_password_hash('table3'), role='employee')
            table4 = User(username='table4', password=generate_password_hash('table4'), role='employee')
            table5 = User(username='table5', password=generate_password_hash('table5'), role='employee')
            table6 = User(username='table6', password=generate_password_hash('table6'), role='employee')
            table7 = User(username='table7', password=generate_password_hash('table7'), role='employee')
            
            db.session.add(admin)
            db.session.add(table1)
            db.session.add(table2)
            db.session.add(table3)
            db.session.add(table4)
            db.session.add(table5)
            db.session.add(table6)
            db.session.add(table7)
            
            db.session.commit()
            logger.debug("Xizmat turlari va foydalanuvchilar muvaffaqiyatli qo'shildi!")
        else:
            logger.debug("Ma'lumotlar bazasida xizmat turlari allaqachon mavjud.")
    except Exception as e:
        logger.error(f"Ma'lumotlar bazasini yaratishda xatolik yuz berdi: {e}")

# Foydalanuvchi autentifikatsiyasi uchun dekorator
def login_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session or session['role'] != role:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Global xatolarni boshqarish
@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Xatolik yuz berdi: {str(e)}")
    return render_template('error.html', error=str(e)), 500

# Tillarni o‘zgartirish
@app.route('/set_language/<lang>')
def set_language(lang):
    session['language'] = lang
    return redirect(request.referrer or url_for('login'))

# Login sahifasi
@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            logger.debug(f"Foydalanuvchi {username} muvaffaqiyatli kirdi")
            if user.role == 'admin':
                return redirect(url_for('admin'))
            elif user.role == 'employee':
                return redirect(url_for('employee'))
        return render_template('index.html', error=_('Noto‘g‘ri foydalanuvchi nomi yoki parol'))
    return render_template('index.html')

# Talaba sahifasi
@app.route('/student')
def student():
    services = ServiceType.query.order_by(ServiceType.name).all()
    return render_template('student.html', services=[(s.id, s.name) for s in services])

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required(['admin', 'employee'])
def edit_profile():
    if request.method == 'POST':
        username = request.form.get('username')
        profile_picture = request.files.get('profile_picture')
        
        # Foydalanuvchi nomini yangilash
        current_user.username = username
        
        # Profil rasmini saqlash
        if profile_picture:
            filename = secure_filename(profile_picture.filename)
            profile_picture.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            session['profile_picture'] = filename
        
        db.session.commit()
        flash('Profil muvaffaqiyatli yangilandi!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('edit_profile.html', profile_picture=session.get('profile_picture'))

# Navbatga qo‘shish (tasdiqlanmaguncha saqlanmaydi)
@app.route('/add_to_queue', methods=['POST'])
def add_to_queue():
    try:
        service_type_id = int(request.form['service_type_id'])
        service = ServiceType.query.get_or_404(service_type_id)
        service_types = ServiceType.query.order_by(ServiceType.name).all()
        prefix = chr(65 + service_types.index(service))
        
        # Bugungi kun uchun navbat raqamlarini tekshirish
        today = datetime.now(pytz.timezone('Asia/Tashkent')).date()
        last_queue = Queue.query.filter(
            Queue.service_type_id == service_type_id,
            Queue.prefix == prefix,
            db.func.date(Queue.created_at) == today
        ).order_by(Queue.queue_number.desc()).first()
        
        new_queue_number = (last_queue.queue_number + 1) if last_queue else 1
        # Navbatni tasdiqlanmaguncha saqlamaymiz, faqat raqamni qaytaramiz
        formatted_queue_number = f"{prefix}{new_queue_number:03d}"
        return jsonify({'queue_number': formatted_queue_number, 'service_type_id': service_type_id, 'prefix': prefix, 'queue_number_int': new_queue_number})
    except Exception as e:
        logger.error(f"Navbat qo‘shishda xatolik: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Navbatni tasdiqlash
@app.route('/confirm_queue', methods=['POST'])
def confirm_queue():
    try:
        data = request.json
        service_type_id = data['service_type_id']
        prefix = data['prefix']
        queue_number = data['queue_number']
        new_queue = Queue(
            queue_number=queue_number,
            prefix=prefix,
            service_type_id=service_type_id,
            status='waiting'
        )
        db.session.add(new_queue)
        db.session.commit()
        logger.debug(f"Navbat tasdiqlandi: {prefix}{queue_number:03d}")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Navbat tasdiqlashda xatolik: {str(e)}")
        return jsonify({'error': str(e)}), 500
# Oldingi navbatlar sonini olish
@app.route('/get_previous_queues/<int:service_type_id>')
def get_previous_queues(service_type_id):
    try:
        count = Queue.query.filter_by(service_type_id=service_type_id, status='waiting').count()
        return jsonify({'previous_count': count})
    except Exception as e:
        logger.error(f"Oldingi navbatlarni olishda xatolik: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Monitor sahifasi
@app.route('/monitor')
def monitor():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    queue_data = Queue.query.filter_by(status='waiting').order_by(Queue.created_at).paginate(page=page, per_page=per_page, error_out=False)
    recent_queues = Queue.query.filter_by(status='served').order_by(Queue.created_at.desc()).limit(5).all()
    return render_template('monitor.html', queue_data=queue_data, recent_queues=recent_queues)

# Monitor sahifasi uchun ma'lumotlarni yangilash
@app.route('/get_queue_data')
def get_queue_data():
    try:
        queue_data = Queue.query.filter_by(status='waiting').order_by(Queue.created_at).limit(10).all()
        html = render_template('_queue_partial.html', queue_data=queue_data)
        return jsonify({'html': html})
    except Exception as e:
        logger.error(f"Navbat ma'lumotlarini yangilashda xatolik: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_employee_queue_data')
def get_employee_queue_data():
    try:
        queue_data = Queue.query.filter_by(status='waiting').order_by(Queue.created_at).limit(10).all()
        html = render_template('_employee_queue_partial.html', queue_data=queue_data)
        return jsonify({'html': html})
    except Exception as e:
        logger.error(f"Xodim navbat ma'lumotlarini yangilashda xatolik: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Xodim sahifasi
@app.route('/employee')
@login_required('employee')
def employee():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    queue_data = Queue.query.filter_by(status='waiting').order_by(Queue.created_at).paginate(page=page, per_page=per_page, error_out=False)
    user = User.query.get(session['user_id'])
    return render_template('employee.html', queue_data=queue_data, username=session['username'], profile_picture=user.profile_picture)

# Navbatni qabul qilish
@app.route('/serve_queue/<int:queue_id>', methods=['POST'])
def serve_queue(queue_id):
    try:
        queue = Queue.query.get_or_404(queue_id)
        queue.status = 'served'
        # Ma'lumotlar bo'sh bo'lsa, standart qiymatlar qo'yamiz
        queue.first_name = request.form.get('first_name', 'Noma\'lum')
        queue.last_name = request.form.get('last_name', 'Noma\'lum')
        queue.group = request.form.get('group', 'Noma\'lum')
        queue.employee = session.get('username', 'Noma\'lum')
        db.session.commit()
        logger.debug(f"Navbat qabul qilindi: {queue.formatted_queue_number}, Xodim: {queue.employee}")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Navbat qabul qilishda xatolik: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Qayta navbatga qo‘shish
@app.route('/requeue/<int:queue_id>', methods=['POST'])
def requeue(queue_id):
    try:
        queue = Queue.query.get_or_404(queue_id)
        queue.created_at = datetime.now(pytz.timezone('Asia/Tashkent'))
        queue.status = 'waiting'
        db.session.commit()
        logger.debug(f"Navbat qayta qo‘shildi: {queue.formatted_queue_number}")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Qayta navbatga qo‘shishda xatolik: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Profil sahifasi
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if User.query.filter_by(username=username).first() and username != user.username:
            return render_template('profile.html', username=user.username, error=_('Bu foydalanuvchi nomi band'), profile_picture=user.profile_picture)
        if password and password != confirm_password:
            return render_template('profile.html', username=user.username, error=_('Parollar mos emas'), profile_picture=user.profile_picture)
        user.username = username
        if password:
            user.password = generate_password_hash(password)

        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and allowed_file(file.filename, file):
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                if file_size > app.config['MAX_CONTENT_LENGTH']:
                    return render_template('profile.html', username=user.username, error=_('Fayl hajmi 5MB dan katta bo‘lmasligi kerak'), profile_picture=user.profile_picture)
                file.seek(0)
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                user.profile_picture = filename

        db.session.commit()
        session['username'] = user.username
        logger.debug(f"Profil yangilandi: {user.username}")
        return render_template('profile.html', username=user.username, success=_('Profil muvaffaqiyatli yangilandi'), profile_picture=user.profile_picture)
    return render_template('profile.html', username=user.username, profile_picture=user.profile_picture)

# Admin sahifasi
@app.route('/admin')
@login_required('admin')
def admin():
    # Statistikani to'g'ri formatlash
    stats_query = db.session.query(
        ServiceType.name.label('service_type'),
        db.func.count(Queue.id).label('count'),
        db.func.strftime('%Y-%m', Queue.created_at).label('month')
    ).join(Queue, Queue.service_type_id == ServiceType.id).filter(Queue.status == 'served').group_by(ServiceType.name, 'month').order_by('month').all()
    
    # Row ob'ektlarini lug'atga aylantirish
    stats = [
        {
            'service_type': stat.service_type,
            'count': stat.count,
            'month': stat.month
        } for stat in stats_query
    ]
    
    # Chart.js uchun ma'lumotlar
    chart_query = db.session.query(
        ServiceType.name.label('service_type'),
        db.func.count(Queue.id).label('count')
    ).join(Queue).filter(Queue.status == 'served').group_by(ServiceType.name).all()
    
    chart_data = [
        {
            'service_type': item.service_type,
            'count': item.count
        } for item in chart_query
    ]
    
    # Xodimlar statistikasi
    employee_stats_query = db.session.query(
        Queue.employee,
        db.func.count(Queue.id).label('count')
    ).filter(Queue.status == 'served', Queue.employee != None).group_by(Queue.employee).all()
    
    employee_stats = [
        {
            'employee': stat.employee,
            'count': stat.count
        } for stat in employee_stats_query
    ]
    
    return render_template(
        'admin.html',
        stats=stats,
        employee_stats=employee_stats,
        chart_data=chart_data
    )
# Foydalanuvchi qo‘shish
@app.route('/admin/add_user', methods=['POST'])
@login_required('admin')
def add_user():
    try:
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        if User.query.filter_by(username=username).first():
            return jsonify({'error': _('Bu foydalanuvchi nomi band')}), 400
        new_user = User(username=username, password=generate_password_hash(password), role=role)
        db.session.add(new_user)
        db.session.commit()
        logger.debug(f"Yangi foydalanuvchi qo‘shildi: {username}")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Foydalanuvchi qo‘shishda xatolik: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Statistika eksport qilish
@app.route('/export_stats', methods=['POST'])
@login_required('admin')
def export_stats():
    try:
        period = request.form['period']
        if period == 'daily':
            stats = db.session.query(
                ServiceType.name.label('service_type'),
                db.func.count(Queue.id).label('count'),
                db.func.strftime('%Y-%m-%d', Queue.created_at).label('date')
            ).join(Queue).filter(Queue.status == 'served').group_by(ServiceType.name, 'date').order_by('date').all()
            headers = ['Xizmat turi', 'Soni', 'Sana']
            rows = [(stat.service_type, stat.count, stat.date) for stat in stats]
        elif period == 'weekly':
            stats = db.session.query(
                ServiceType.name.label('service_type'),
                db.func.count(Queue.id).label('count'),
                db.func.strftime('%Y-%W', Queue.created_at).label('week')
            ).join(Queue).filter(Queue.status == 'served').group_by(ServiceType.name, 'week').order_by('week').all()
            headers = ['Xizmat turi', 'Soni', 'Hafta']
            rows = [(stat.service_type, stat.count, stat.week) for stat in stats]
        else:
            stats = db.session.query(
                ServiceType.name.label('service_type'),
                db.func.count(Queue.id).label('count'),
                db.func.strftime('%Y-%m', Queue.created_at).label('month')
            ).join(Queue).filter(Queue.status == 'served').group_by(ServiceType.name, 'month').order_by('month').all()
            headers = ['Xizmat turi', 'Soni', 'Oy']
            rows = [(stat.service_type, stat.count, stat.month) for stat in stats]
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(rows)
        return send_file(
            StringIO(output.getvalue()),
            mimetype='text/csv',
            as_attachment=True,
            download_name='stats.csv'
        )
    except Exception as e:
        logger.error(f"Statistikani eksport qilishda xatolik: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Eski navbatlarni tozalash
@app.route('/clean_old_queues', methods=['POST'])
@login_required('admin')
def clean_old_queues():
    try:
        threshold_date = datetime.now(pytz.timezone('Asia/Tashkent')) - timedelta(days=30)
        deleted = Queue.query.filter(Queue.status == 'served', Queue.created_at < threshold_date).delete()
        db.session.commit()
        logger.debug(f"{deleted} ta eski navbat o‘chirildi")
        return jsonify({'success': True, 'deleted': deleted})
    except Exception as e:
        logger.error(f"Eski navbatlarni tozalashda xatolik: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Navbat sonini olish
@app.route('/get_queue_count')
def get_queue_count():
    try:
        count = Queue.query.filter_by(status='waiting').count()
        return jsonify({'count': count})
    except Exception as e:
        logger.error(f"Navbat sonini olishda xatolik: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Chiqish
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('role', None)
    logger.debug("Foydalanuvchi chiqdi")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)