from flask import Flask, render_template, request, redirect, url_for, flash, session
import pandas as pd
import os
import subprocess
import sys

app = Flask(__name__) # type: ignore
app.config['APP_NAME'] = os.environ.get('APP_NAME', 'LibraryManagement')
app.secret_key = 'book'

# Define data directory paths
DATA_DIR = 'data'  # Verzeichnis für Daten
USERS_FILE = f'{DATA_DIR}/users.csv'  # CSV-Datei für Benutzerdaten
BOOKS_FILE = f'{DATA_DIR}/books.csv'  # CSV-Datei für Bücherdaten

def initialize_app():
    """
    Initialisiert die Anwendung und erstellt die erforderlichen Datendateien.
    Erstellt das Datenverzeichnis und initialisiert leere CSV-Dateien für
    Benutzer und Bücher, falls diese noch nicht existieren.
    """
    app = Flask(__name__)
    app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-secret-key",  # Required for sessions
        "SESSION_TYPE": "filesystem",     # Required for session backend
        "DATA_DIR": "test_data",
        "USERS_FILE": "test_data/users.csv",
        "BOOKS_FILE": "test_data/books.csv"
    })
    
    # Create test data directory
    os.makedirs(app.config["DATA_DIR"], exist_ok=True)
    
    # Initialize users file if it doesn't exist
    users_file = app.config["USERS_FILE"]
    if not os.path.exists(users_file):
        df = pd.DataFrame({
            'id': [],           # Eindeutige Benutzer-ID
            'name': [],         # Benutzername
            'email': [],        # E-Mail-Adresse
            'password': [],     # Passwort (im Klartext gespeichert!)
            'role': []          # Benutzerrolle (user/staff)
        })
        df.to_csv(users_file, index=False)
    
    # Initialize books file if it doesn't exist
    books_file = app.config["BOOKS_FILE"]
    if not os.path.exists(books_file):
        df = pd.DataFrame({
            'id': [],           # Eindeutige Buch-ID
            'title': [],        # Titel des Buches
            'author': [],       # Autor des Buches
            'year': [],         # Erscheinungsjahr
            'status': []        # Status (verfügbar/ausgeliehen)
        })
        df.to_csv(books_file, index=False)
    
    return app

# Data manipulation functions
def get_users():
    """
    Liest alle Benutzerdaten aus der CSV-Datei.
    Returns:
        DataFrame mit allen Benutzern
    """
    return pd.read_csv(USERS_FILE)

def get_books():
    """
    Liest alle Bücherdaten aus der CSV-Datei.
    Returns:
        DataFrame mit allen Büchern
    """
    return pd.read_csv(BOOKS_FILE)

def save_users(df):
    """
    Speichert die aktualisierten Benutzerdaten in die CSV-Datei.
    Args:
        df (DataFrame): Aktualisierter DataFrame mit Benutzerdaten
    """
    df.to_csv(USERS_FILE, index=False)

def save_books(df):
    """
    Speichert die aktualisierten Bücherdaten in die CSV-Datei.
    Args:
        df (DataFrame): Aktualisierter DataFrame mit Bücherdaten
    """
    df.to_csv(BOOKS_FILE, index=False)

# Main routes
@app.route('/')
def index():
    """
    Hauptseite der Bibliotheksanwendung.
    
    Zeigt alle verfügbaren Bücher an und ermöglicht die Suche.
    Returns:
        Rendered template mit Bücherverzeichnis
    """
    books = get_books()
    return render_template('index.html', books=books)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Benutzerregistrierungsroute.
    
    Behandelt GET-Anfragen für das Registrierungsformular und 
    POST-Anfragen zur Verarbeitung der Registrierung.
    """
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']  # user oder staff
        
        users = get_users()
        if email in users['email'].values:
            flash('Diese E-Mail-Adresse ist bereits registriert.', 'danger')
            return redirect(url_for('register'))
        
        new_id = int(users['id'].max()) + 1 if not users.empty else 1
        new_user = {
            'id': new_id,
            'name': name,
            'email': email,
            'password': password,
            'role': role
        }
        users = pd.concat([users, pd.DataFrame([new_user])],
                         ignore_index=True)
        save_users(users)
        flash('Registrierung erfolgreich!', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Benutzereinlogik.
    
    Behandelt Login-Versuche und verwaltet die Sessions.
    """
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        users = get_users()
        user = users[users['email'] == email]
        
        if not user.empty and user.iloc[0]['password'] == password:
            session['user_id'] = int(user.iloc[0]['id'])
            session['user_name'] = user.iloc[0]['name']
            session['role'] = user.iloc[0]['role']
            flash('Willkommen zurück!', 'success')
            return redirect(url_for('index'))
        
        flash('Falsche E-Mail oder Passwort.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """
    Benutzerauslogik.
    
    Löscht alle Session-Daten und leitet zur Hauptseite weiter.
    """
    session.clear()
    flash('Sie wurden erfolgreich ausgeloggt.', 'success')
    return redirect(url_for('index'))

# Book management routes
@app.route('/books', methods=['GET', 'POST'])
def books():
    """
    Bibliotheksverwaltung für Mitarbeiter.
    
    Zeigt alle Bücher an und ermöglicht deren Verwaltung.
    Nur zugänglich für autorisierte Mitarbeiter.
    """
    if 'user_id' not in session or session.get('role') != 'staff':
        flash('Zugriff nicht erlaubt.', 'danger')
        return redirect(url_for('login'))
    
    books = get_books()
    return render_template('books.html', books=books)





def install_packages():
    # List of packages to install
    packages = [
        'pip',  # First upgrade pip
        'flask',
        'pandas',
        'pytest'
    ]
    
    try:
        # Upgrade pip first
        print("Upgrading pip...")
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        
        # Install remaining packages
        for package in packages[1:]:  # Skip pip since we already upgraded it
            print(f"Installing {package}...")
            subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)
            print(f"{package} installed successfully!")
            
        print("\nAll packages installed successfully!")
        
    except subprocess.CalledProcessError as e:
        print(f"Error installing packages: {e}")
        print("Please run the application with administrator privileges.")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == '__main__':
    print("Initializing application...")
    install_packages()
    initialize_app()
    app.run(debug=True)