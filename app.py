import sqlite3
from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import requests


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fm.db'
app.config['SECRET_KEY'] = 'thisisasecret'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Actor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)

class Director(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)

class Film(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    director_id = db.Column(db.Integer, db.ForeignKey('director.id'), nullable=False)
    release_year = db.Column(db.Integer, nullable=False)

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey('actor.id'), nullable=False)
    film_id = db.Column(db.Integer, db.ForeignKey('film.id'), nullable=False)
    character_name = db.Column(db.String(100), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('base'))
        else:
            flash('Login failed. Check your username and password.')

    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('index.html')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/base')
@login_required
def base():
    return render_template('base.html')

@app.route('/actors')
@login_required
def actors():
    actors = Actor.query.all()
    return render_template('actors.html', actors=actors)

@app.route('/directors')
@login_required
def directors():
    directors = Director.query.all()
    return render_template('directors.html', directors=directors)

@app.route('/films')
@login_required
def films():
    films = Film.query.all()
    return render_template('films.html', films=films)


@app.route('/film/<int:film_id>')
@login_required
def film(film_id):
    film = Film.query.get_or_404(film_id)
    director = Director.query.get(film.director_id)
    actors = Role.query.filter_by(film_id=film_id).join(Actor).all()
    return render_template('film.html', film=film, director=director, actors=actors)


@app.route('/add_movies_to_database')
def add_movies_to_database_route():
    add_movies_to_database()
    return redirect(url_for('films'))

def add_movies_to_database():
    # Connect to SQLite database
    conn = sqlite3.connect('fm.db')
    cur = conn.cursor()

    # API request to retrieve movie data
    api_key = '561b14c296cb3b8afba009550467b273'
    search_term = ''
    url = f'https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={search_term}'
    response = requests.get(url)
    data = response.json()

    # Parse and insert movie data into database
    if 'results' in data:
        for movie in data['results']:
            movie_id = movie['id']
            title = movie['title']
            release_year = int(movie['release_date'][:4])
            
            # Fetch movie details to get director information
            movie_details_url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&append_to_response=credits'
            movie_details_response = requests.get(movie_details_url)
            movie_details_data = movie_details_response.json()

            # Find the director from the movie's crew
            director_name = None
            for crew_member in movie_details_data['credits']['crew']:
                if crew_member['job'] == 'Director':
                    director_name = crew_member['name']
                    break

            # Insert director into the Director table if not exists
            if director_name:
                first_name, last_name = director_name.split(' ', 1)
                cur.execute('INSERT OR IGNORE INTO Director (first_name, last_name) VALUES (?, ?)', (first_name, last_name))

                # Get the director ID
                cur.execute('SELECT id FROM Director WHERE first_name=? AND last_name=?', (first_name, last_name))
                director_id = cur.fetchone()[0]
            else:
                director_id = None

            # Insert movie data into the Film table
            cur.execute('INSERT INTO Film (title, director_id, release_year) VALUES (?, ?, ?)', (title, director_id, release_year))

    else:
        print('No results found')
        return redirect(url_for('home'))

    # Commit changes and close connection
    conn.commit()
    conn.close()



with app.app_context():
    db.create_all()
    app.run(debug=True)



