from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import os
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# Database initialization
def init_db():
    if not os.path.exists('database.db'):
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE urls (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        url TEXT UNIQUE,
                        title TEXT,
                        description TEXT,
                        favicon TEXT,
                        keywords TEXT,
                        rank INTEGER DEFAULT 0,
                        clicks INTEGER DEFAULT 0
                    )''')
        conn.commit()
        conn.close()

init_db()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM urls")
    urls = c.fetchall()
    conn.close()
    return render_template('admin.html', urls=urls)

@app.route('/results', methods=['GET'])
def results():
    query = request.args.get('q', '')
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM urls WHERE keywords LIKE ? OR description LIKE ? ORDER BY rank DESC", (f"%{query}%", f"%{query}%"))
    results = c.fetchall()
    conn.close()
    return render_template('results.html', query=query, results=results)

@app.route('/add_url', methods=['POST'])
def add_url():
    data = request.form
    url = data.get('url')
    title = data.get('title')
    description = data.get('description')
    favicon = data.get('favicon')
    keywords = data.get('keywords')

    # Auto-fetch data if crawler toggle is enabled
    if data.get('crawler') == 'on':
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            title = title or soup.title.string if soup.title else ''
            description = description or soup.find('meta', {'name': 'description'})
            description = description['content'] if description else ''
            favicon = favicon or urlparse(url).scheme + '://' + urlparse(url).netloc + '/favicon.ico'
        except Exception as e:
            print(f"Error fetching URL data: {e}")

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    try:
        c.execute('''INSERT INTO urls (url, title, description, favicon, keywords) VALUES (?, ?, ?, ?, ?)''',
                  (url, title, description, favicon, keywords))
        conn.commit()
    except sqlite3.IntegrityError:
        print("URL already exists in the database.")
    conn.close()
    return redirect(url_for('admin'))

@app.route('/update_url', methods=['POST'])
def update_url():
    data = request.form
    url_id = data.get('id')
    url = data.get('url')
    title = data.get('title')
    description = data.get('description')
    favicon = data.get('favicon')
    keywords = data.get('keywords')
    rank = data.get('rank')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''UPDATE urls SET url = ?, title = ?, description = ?, favicon = ?, keywords = ?, rank = ? WHERE id = ?''',
              (url, title, description, favicon, keywords, rank, url_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/vote', methods=['POST'])
def vote():
    data = request.json
    url_id = data.get('id')
    vote_type = data.get('type')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    if vote_type == 'up':
        c.execute("UPDATE urls SET rank = rank + 1 WHERE id = ?", (url_id,))
    elif vote_type == 'down':
        c.execute("UPDATE urls SET rank = rank - 1 WHERE id = ?", (url_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True)
