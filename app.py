"""
Icarus Flask Application
A sanctuary for human creativity
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

# Initialize Flask app
app = Flask(__name__)
app.config.from_object('config.Config')

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'signin'
login_manager.login_message = 'Please sign in to access this page.'
login_manager.login_message_category = 'info'

# ============================================================================
# DATABASE MODELS
# ============================================================================

class User(UserMixin, db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100), nullable=True)
    username = db.Column(db.String(50), unique=True, nullable=True)
    bio = db.Column(db.String(500), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    theme = db.Column(db.String(20), default='earth')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    likes = db.relationship('Like', backref='user', lazy='dynamic')
    bookmarks = db.relationship('Bookmark', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_display_name(self):
        return self.name or self.username or self.email.split('@')[0]
    
    def get_initials(self):
        name = self.get_display_name()
        return name[0].upper() if name else '?'
    
    def get_handle(self):
        if self.username:
            return f"@{self.username}"
        return f"@{self.email.split('@')[0]}"
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'username': self.username,
            'bio': self.bio,
            'theme': self.theme,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class WaitlistEntry(db.Model):
    """Waitlist entries for early access"""
    __tablename__ = 'waitlist'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    role = db.Column(db.String(50), nullable=True)
    source = db.Column(db.String(50), default='waitlist-page')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notified = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'source': self.source,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'notified': self.notified
        }


class Post(db.Model):
    """User posts/creations"""
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=True)
    media_type = db.Column(db.String(20), default='text')
    media_url = db.Column(db.String(500), nullable=True)
    category = db.Column(db.String(50), default='art')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    likes = db.relationship('Like', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    bookmarks = db.relationship('Bookmark', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    
    def like_count(self):
        return self.likes.count()
    
    def bookmark_count(self):
        return self.bookmarks.count()
    
    def is_liked_by(self, user):
        if not user or not user.is_authenticated:
            return False
        return self.likes.filter_by(user_id=user.id).first() is not None
    
    def is_bookmarked_by(self, user):
        if not user or not user.is_authenticated:
            return False
        return self.bookmarks.filter_by(user_id=user.id).first() is not None
    
    def to_dict(self, user=None):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'author_name': self.author.get_display_name(),
            'author_handle': self.author.get_handle(),
            'author_initials': self.author.get_initials(),
            'content': self.content,
            'media_type': self.media_type,
            'media_url': self.media_url,
            'category': self.category,
            'likes': self.like_count(),
            'bookmarks': self.bookmark_count(),
            'is_liked': self.is_liked_by(user) if user else False,
            'is_bookmarked': self.is_bookmarked_by(user) if user else False,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'time_ago': self.time_ago()
        }
    
    def time_ago(self):
        now = datetime.utcnow()
        diff = now - self.created_at
        if diff.days > 365:
            return f"{diff.days // 365}y"
        elif diff.days > 30:
            return f"{diff.days // 30}mo"
        elif diff.days > 0:
            return f"{diff.days}d"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600}h"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60}m"
        else:
            return "now"


class Like(db.Model):
    __tablename__ = 'likes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id'),)


class Bookmark(db.Model):
    __tablename__ = 'bookmarks'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id'),)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ============================================================================
# PAGE ROUTES
# ============================================================================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if current_user.is_authenticated:
        return redirect(url_for('feed'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash('Welcome back!', 'success')
            return redirect(next_page if next_page else url_for('feed'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('signin.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('feed'))
    return render_template('signup.html')


@app.route('/waitlist')
def waitlist():
    return render_template('waitlist.html')


@app.route('/dashboard')
@login_required
def dashboard():
    post_count = Post.query.filter_by(user_id=current_user.id).count()
    art_count = Post.query.filter_by(user_id=current_user.id, category='art').count()
    music_count = Post.query.filter_by(user_id=current_user.id, category='music').count()
    film_count = Post.query.filter_by(user_id=current_user.id, category='film').count()
    
    stats = {'total': post_count, 'art': art_count, 'music': music_count, 'film': film_count}
    recent_posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.created_at.desc()).limit(5).all()
    
    return render_template('dashboard.html', user=current_user, stats=stats, recent_posts=recent_posts)


@app.route('/feed')
@app.route('/feed/<theme>')
@login_required
def feed(theme=None):
    if theme is None:
        theme = current_user.theme if current_user.is_authenticated else 'earth'

    posts = Post.query.order_by(Post.created_at.desc()).limit(50).all()

    theme_map = {
        'dark': 'dark/feed.html',
        'light': 'light/feed.html',
        'earth': 'forest/feed.html',
        'forest': 'forest/feed.html'
    }

    template = theme_map.get(theme, 'forest/feed.html')
    return render_template(template, user=current_user, current_theme=theme, posts=posts)


@app.route('/settings')
@login_required
def settings():
    # Redirect to feed with settings modal auto-open parameter
    theme = current_user.theme if current_user.is_authenticated else 'earth'
    return redirect(url_for('feed', theme=theme, open_settings='true'))


@app.route('/explore')
@app.route('/explore/<theme>')
@login_required
def explore(theme=None):
    if theme is None:
        theme = current_user.theme if current_user.is_authenticated else 'earth'

    posts = Post.query.order_by(Post.created_at.desc()).limit(50).all()

    theme_map = {
        'dark': 'dark/explore.html',
        'light': 'light/explore.html',
        'earth': 'forest/explore.html',
        'forest': 'forest/explore.html'
    }

    template = theme_map.get(theme, 'forest/explore.html')
    return render_template(template, user=current_user, current_theme=theme, posts=posts)


@app.route('/bookmarks')
@app.route('/bookmarks/<theme>')
@login_required
def bookmarks_page(theme=None):
    if theme is None:
        theme = current_user.theme if current_user.is_authenticated else 'earth'

    bookmarked_posts = Post.query.join(Bookmark).filter(
        Bookmark.user_id == current_user.id
    ).order_by(Bookmark.created_at.desc()).all()

    theme_map = {
        'dark': 'dark/bookmarks.html',
        'light': 'light/bookmarks.html',
        'earth': 'forest/bookmarks.html',
        'forest': 'forest/bookmarks.html'
    }
    template = theme_map.get(theme, 'forest/bookmarks.html')

    return render_template(template, user=current_user, current_theme=theme, posts=bookmarked_posts, page_title='Bookmarks')


@app.route('/profile')
@app.route('/profile/<theme>')
@login_required
def profile(theme=None):
    if theme is None:
        theme = current_user.theme if current_user.is_authenticated else 'earth'

    posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.created_at.desc()).all()

    theme_map = {
        'dark': 'dark/profile.html',
        'light': 'light/profile.html',
        'earth': 'forest/profile.html',
        'forest': 'forest/profile.html'
    }
    template = theme_map.get(theme, 'forest/profile.html')

    return render_template(template, user=current_user, current_theme=theme, posts=posts, page_title=f"{current_user.get_display_name()}'s Profile")


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been signed out.', 'info')
    return redirect(url_for('index'))


# ============================================================================
# API ROUTES
# ============================================================================

@app.route('/api/signup', methods=['POST'])
def api_signup():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    name = data.get('name', '').strip()
    phone = data.get('phone', '').strip()
    theme = data.get('theme', 'earth')
    
    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password are required'}), 400
    
    if len(password) < 8:
        return jsonify({'success': False, 'error': 'Password must be at least 8 characters'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'error': 'Email already registered'}), 409
    
    base_username = email.split('@')[0].lower()
    username = base_username
    counter = 1
    while User.query.filter_by(username=username).first():
        username = f"{base_username}{counter}"
        counter += 1
    
    user = User(email=email, name=name if name else None, username=username, phone=phone if phone else None, theme=theme)
    user.set_password(password)
    
    try:
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return jsonify({'success': True, 'message': 'Account created successfully', 'user': user.to_dict(), 'redirect': url_for('feed')}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Database error'}), 500


@app.route('/api/signin', methods=['POST'])
def api_signin():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    remember = data.get('remember', False)
    
    user = User.query.filter_by(email=email).first()
    
    if user and user.check_password(password):
        login_user(user, remember=remember)
        return jsonify({'success': True, 'message': 'Signed in successfully', 'user': user.to_dict(), 'redirect': url_for('feed')}), 200
    else:
        return jsonify({'success': False, 'error': 'Invalid email or password'}), 401


@app.route('/waitlist/submit', methods=['POST'])
def waitlist_submit():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    email = data.get('email', '').strip().lower()
    name = data.get('name', '').strip()
    role = data.get('role', '').strip()
    source = data.get('source', 'waitlist-page')
    
    if not email:
        return jsonify({'success': False, 'error': 'Email is required'}), 400
    
    existing = WaitlistEntry.query.filter_by(email=email).first()
    if existing:
        return jsonify({'success': True, 'message': 'You\'re already on the waitlist!'}), 200
    
    entry = WaitlistEntry(email=email, name=name if name else None, role=role if role else None, source=source)
    
    try:
        db.session.add(entry)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Successfully joined the waitlist', 'entry': entry.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Database error'}), 500


@app.route('/api/user', methods=['GET'])
@login_required
def get_current_user():
    return jsonify({'success': True, 'user': current_user.to_dict()})


@app.route('/api/user/profile', methods=['PUT'])
@login_required
def update_profile():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    if 'name' in data:
        current_user.name = data['name'].strip() if data['name'] else None
    
    if 'username' in data:
        new_username = data['username'].strip().lower()
        if new_username:
            existing = User.query.filter(User.username == new_username, User.id != current_user.id).first()
            if existing:
                return jsonify({'success': False, 'error': 'Username already taken'}), 409
            current_user.username = new_username
    
    if 'bio' in data:
        current_user.bio = data['bio'].strip() if data['bio'] else None
    
    if 'email' in data:
        new_email = data['email'].strip().lower()
        if new_email and new_email != current_user.email:
            existing = User.query.filter(User.email == new_email, User.id != current_user.id).first()
            if existing:
                return jsonify({'success': False, 'error': 'Email already in use'}), 409
            current_user.email = new_email
    
    try:
        db.session.commit()
        return jsonify({'success': True, 'message': 'Profile updated successfully', 'user': current_user.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Database error'}), 500


@app.route('/api/user/password', methods=['PUT'])
@login_required
def update_password():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    
    if not current_user.check_password(current_password):
        return jsonify({'success': False, 'error': 'Current password is incorrect'}), 401
    
    if len(new_password) < 8:
        return jsonify({'success': False, 'error': 'New password must be at least 8 characters'}), 400
    
    current_user.set_password(new_password)
    
    try:
        db.session.commit()
        return jsonify({'success': True, 'message': 'Password updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Database error'}), 500


@app.route('/api/user/theme', methods=['PUT'])
@login_required
def update_theme():
    data = request.get_json()
    theme = data.get('theme', 'earth')
    
    if theme not in ['dark', 'light', 'earth']:
        return jsonify({'success': False, 'error': 'Invalid theme'}), 400
    
    current_user.theme = theme
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Theme updated', 'theme': theme})


@app.route('/api/posts', methods=['GET'])
@login_required
def get_posts():
    category = request.args.get('category', None)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = Post.query
    if category:
        query = query.filter_by(category=category)
    
    posts = query.order_by(Post.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'success': True,
        'posts': [post.to_dict(current_user) for post in posts.items],
        'total': posts.total,
        'pages': posts.pages,
        'current_page': page
    })


@app.route('/api/posts', methods=['POST'])
@login_required
def create_post():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    content = data.get('content', '').strip()
    category = data.get('category', 'art')
    media_type = data.get('media_type', 'text')
    media_url = data.get('media_url', '').strip()
    
    if not content and not media_url:
        return jsonify({'success': False, 'error': 'Content or media is required'}), 400
    
    if category not in ['art', 'music', 'film']:
        category = 'art'
    
    post = Post(user_id=current_user.id, content=content, category=category, media_type=media_type, media_url=media_url if media_url else None)
    
    try:
        db.session.add(post)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Post created successfully', 'post': post.to_dict(current_user)}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Database error'}), 500


@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    if post.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        db.session.delete(post)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Post deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Database error'}), 500


@app.route('/api/posts/<int:post_id>/like', methods=['POST'])
@login_required
def toggle_like(post_id):
    post = Post.query.get_or_404(post_id)
    existing_like = Like.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    
    try:
        if existing_like:
            db.session.delete(existing_like)
            db.session.commit()
            return jsonify({'success': True, 'liked': False, 'likes': post.like_count()})
        else:
            like = Like(user_id=current_user.id, post_id=post_id)
            db.session.add(like)
            db.session.commit()
            return jsonify({'success': True, 'liked': True, 'likes': post.like_count()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Database error'}), 500


@app.route('/api/posts/<int:post_id>/bookmark', methods=['POST'])
@login_required
def toggle_bookmark(post_id):
    post = Post.query.get_or_404(post_id)
    existing_bookmark = Bookmark.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    
    try:
        if existing_bookmark:
            db.session.delete(existing_bookmark)
            db.session.commit()
            return jsonify({'success': True, 'bookmarked': False, 'bookmarks': post.bookmark_count()})
        else:
            bookmark = Bookmark(user_id=current_user.id, post_id=post_id)
            db.session.add(bookmark)
            db.session.commit()
            return jsonify({'success': True, 'bookmarked': True, 'bookmarks': post.bookmark_count()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Database error'}), 500


@app.route('/api/waitlist', methods=['GET'])
@login_required
def get_waitlist():
    entries = WaitlistEntry.query.order_by(WaitlistEntry.created_at.desc()).all()
    return jsonify({'success': True, 'count': len(entries), 'entries': [entry.to_dict() for entry in entries]})


@app.route('/posts/<path:subpath>/<filename>')
def serve_post_media(subpath, filename):
    """Serve media files from the posts directory"""
    posts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'posts')
    return send_from_directory(os.path.join(posts_dir, subpath), filename)


@app.route('/api/user/delete', methods=['DELETE'])
@login_required
def delete_account():
    data = request.get_json()
    password = data.get('password', '')
    
    if not current_user.check_password(password):
        return jsonify({'success': False, 'error': 'Incorrect password'}), 401
    
    try:
        Post.query.filter_by(user_id=current_user.id).delete()
        Like.query.filter_by(user_id=current_user.id).delete()
        Bookmark.query.filter_by(user_id=current_user.id).delete()
        db.session.delete(current_user)
        db.session.commit()
        logout_user()
        return jsonify({'success': True, 'message': 'Account deleted successfully', 'redirect': url_for('index')})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Database error'}), 500


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': 'Not found'}), 404
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
    return render_template('500.html'), 500


@app.context_processor
def inject_user():
    return dict(current_user=current_user)


def init_db():
    with app.app_context():
        # Create instance folder to prevent sqlite3.OperationalError
        import os
        instance_path = os.path.join(app.root_path, 'instance')
        if not os.path.exists(instance_path):
            try:
                os.makedirs(instance_path)
            except OSError:
                pass
                
        db.create_all()
        print("Database initialized successfully!")


def seed_demo_data():
    with app.app_context():
        if Post.query.count() > 0:
            return
        
        demo_user = User.query.filter_by(email='demo@icarus.art').first()
        if not demo_user:
            demo_user = User(email='demo@icarus.art', name='Demo Artist', username='demoartist', bio='Exploring the boundaries of human creativity', theme='earth')
            demo_user.set_password('demo1234')
            db.session.add(demo_user)
            db.session.commit()
        
        demo_posts = [
            {'content': 'Just finished this piece after 3 weeks of work. Every brushstroke was intentional, every color carefully chosen. This is what human art looks like. 🎨', 'category': 'art'},
            {'content': 'New composition dropping soon. Wrote every note by hand, recorded with real instruments. No algorithms, just pure human expression. 🎵', 'category': 'music'},
            {'content': 'Behind the scenes of my latest short film. 6 months of planning, 2 weeks of shooting, 3 months of editing. Made by humans, for humans. 🎬', 'category': 'film'},
            {'content': 'The process matters as much as the result. Sharing my sketchbook pages from this morning\'s session.', 'category': 'art'},
            {'content': 'Collaboration with @humanmusician on our acoustic album. Pure, unfiltered creativity.', 'category': 'music'},
        ]
        
        for post_data in demo_posts:
            post = Post(user_id=demo_user.id, content=post_data['content'], category=post_data['category'], media_type='text')
            db.session.add(post)
        
        db.session.commit()
        print("Demo data seeded successfully!")


if __name__ == '__main__':
    init_db()
    seed_demo_data()
    app.run(debug=True, host='0.0.0.0', port=5000)