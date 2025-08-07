import os
import uuid
import aiosqlite
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_very_secret_key_here'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'mp4'}
app.config['ADMIN_USERNAME'] = 'admin'
app.config['ADMIN_PASSWORD'] = generate_password_hash('securepassword123')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

async def init_db():
    async with aiosqlite.connect('services.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                price INTEGER NOT NULL,
                image_path TEXT,
                video_path TEXT,
                category TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        cursor = await db.execute('SELECT * FROM users WHERE username = ?', (app.config['ADMIN_USERNAME'],))
        if not await cursor.fetchone():
            await db.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                           (app.config['ADMIN_USERNAME'], app.config['ADMIN_PASSWORD']))
        await db.commit()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def save_file(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{uuid.uuid4()}.{file.filename.rsplit('.', 1)[1].lower()}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return f"uploads/{filename}"
    return None

@app.route('/login', methods=['GET', 'POST'])
async def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        async with aiosqlite.connect('services.db') as db:
            cursor = await db.execute('SELECT * FROM users WHERE username = ?', (username,))
            user = await cursor.fetchone()

        if user and check_password_hash(user[2], password):
            session['logged_in'] = True
            flash('Вы успешно вошли в систему', 'success')
            return jsonify({'success': True, 'redirect': url_for('admin_dashboard')})
        return jsonify({'success': False, 'message': 'Неверные учетные данные'})
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('Вы успешно вышли из системы', 'success')
    return redirect(url_for('home'))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/category/<category>')
async def category_page(category):
    async with aiosqlite.connect('services.db') as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('SELECT * FROM services WHERE category = ?', (category,))
        services = await cursor.fetchall()

    category_names = {
        'cosmetology': 'Косметология',
        'piercing': 'Пирсинг',
        'lami': 'Лами'
    }
    return render_template('category.html',
                         services=services,
                         category=category_names.get(category, category))

@app.route('/admin')
async def admin_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('admin/dashboard.html')

@app.route('/admin/<category>')
async def admin_category(category):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    async with aiosqlite.connect('services.db') as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('SELECT * FROM services WHERE category = ?', (category,))
        services = await cursor.fetchall()

    category_names = {
        'cosmetology': 'Косметология',
        'piercing': 'Пирсинг',
        'lami': 'Лами'
    }
    return render_template('admin/category.html',
                         services=services,
                         category=category,
                         category_name=category_names.get(category, category))

@app.route('/admin/add_service', methods=['GET', 'POST'])
async def add_service():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            title = request.form['title']
            description = request.form['description']
            price = int(request.form['price'])
            category = request.form['category']

            image = request.files.get('image')
            video = request.files.get('video')

            image_path = save_file(image) if image else None
            video_path = save_file(video) if video else None

            async with aiosqlite.connect('services.db') as db:
                await db.execute('''
                    INSERT INTO services (title, description, price, image_path, video_path, category)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (title, description, price, image_path, video_path, category))
                await db.commit()

            flash('Услуга успешно добавлена', 'success')
            return jsonify({'success': True, 'redirect': url_for('admin_category', category=category)})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})

    return render_template('admin/add_service.html')

@app.route('/admin/edit_service/<int:service_id>', methods=['GET', 'POST'])
async def edit_service(service_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    async with aiosqlite.connect('services.db') as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('SELECT * FROM services WHERE id = ?', (service_id,))
        service = await cursor.fetchone()

    if request.method == 'POST':
        try:
            title = request.form['title']
            description = request.form['description']
            price = int(request.form['price'])
            category = request.form['category']

            image = request.files.get('image')
            video = request.files.get('video')

            image_path = service['image_path']
            if image and image.filename:
                image_path = save_file(image)

            video_path = service['video_path']
            if video and video.filename:
                video_path = save_file(video)

            async with aiosqlite.connect('services.db') as db:
                await db.execute('''
                    UPDATE services 
                    SET title = ?, description = ?, price = ?, image_path = ?, video_path = ?, category = ?
                    WHERE id = ?
                ''', (title, description, price, image_path, video_path, category, service_id))
                await db.commit()

            flash('Услуга успешно обновлена', 'success')
            return jsonify({'success': True, 'redirect': url_for('admin_category', category=category)})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})

    return render_template('admin/edit_service.html', service=dict(service))

@app.route('/admin/delete_service/<int:service_id>')
async def delete_service(service_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    async with aiosqlite.connect('services.db') as db:
        cursor = await db.execute('SELECT category FROM services WHERE id = ?', (service_id,))
        category = (await cursor.fetchone())[0]
        await db.execute('DELETE FROM services WHERE id = ?', (service_id,))
        await db.commit()

    flash('Услуга успешно удалена', 'success')
    return redirect(url_for('admin_category', category=category))

@app.before_request
async def before_first_request():
    await init_db()

if __name__ == '__main__':
    app.run(debug=True)