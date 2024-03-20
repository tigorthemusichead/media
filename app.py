import sqlite3
import os
import wave
import json
import time
from vosk import Model, KaldiRecognizer, SetLogLevel
from flask import Flask, request, abort, render_template, g, redirect, session
from pydub import AudioSegment
from werkzeug.utils import secure_filename
from flask_bcrypt import Bcrypt

DATABASE = './db/database.db'

app = Flask(__name__)

app.secret_key = 'BAD_SECRET_KEY'

bcrypt = Bcrypt(app)

def get_db():
  db = getattr(g, '_database', None)
  if db is None:
    db = g._database = sqlite3.connect(DATABASE)
  return db


@app.teardown_appcontext
def close_connection(exception):
  db = getattr(g, '_database', None)
  if db is not None:
    db.close()

def query_db(query, args=(), one=False):
  cur = get_db().execute(query, args)
  rv = cur.fetchall()
  cur.close()
  print(rv)
  return (rv[0] if rv else None) if one else rv

def init_db():
  with app.app_context():
    db = get_db()
    with app.open_resource('./db/schema.sql', mode='r') as f:
      db.cursor().executescript(f.read())
    db.commit()

def process_file(file_name):
  given_audio = AudioSegment.from_file(file_name, format=file_name[-3:])
  given_audio = given_audio.set_channels(1)
  given_audio.export(f"{file_name[:-4]}.wav", format="wav")
  SetLogLevel(0)

  wf = wave.open(f"{file_name[:-4]}.wav", "rb")
  file = open(f"{file_name[:-4]}.txt", "w")
  if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
    print("Audio file must be WAV format mono PCM.")
    exit(1)

  model = Model("model")
  rec = KaldiRecognizer(model, wf.getframerate())
  rec.SetWords(True)
  rec.SetPartialWords(True)
  while True:
    data = wf.readframes(4000)
    if len(data) == 0:
      break
    if rec.AcceptWaveform(data):
      file.write(json.loads(rec.Result())["text"] + "\n\n")
  file.close()
  os.remove(f"{file_name[:-4]}.wav")
  os.remove(file_name)
  file = open(f"{file_name[:-4]}.txt", "r")
  text = file.read()
  file.close()
  try:
    with sqlite3.connect("./db/database.db") as con:
      cur = con.cursor()
      cur.execute('INSERT INTO "results" ("filename", "username") VALUES(?, ?)', (f"{file_name[:-4]}.txt", session['name']))
      rv = cur.fetchall()
      con.commit()
      print(rv)
  except Exception as error:
    print(error)
  return text

@app.route('/logout', methods=['GET'])
def logout():
  session.pop('name', None)
  return redirect('/login', code=302)

@app.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    username = request.form['name']
    password = request.form['password']
    if username == "" or password == "":
      return render_template('login.html', error={'login': 'Please fill all fields'})
    try:
      with sqlite3.connect("./db/database.db") as con:
        cur = con.cursor()
        cur.execute('SELECT * FROM "users" WHERE name=?', (username,))
        rv = cur.fetchall()
        con.commit()
        print(rv)
        password_hash = rv[0][2]
        if rv[0] != None and bcrypt.check_password_hash(password_hash, password):
          session['name'] = username
          return redirect('/')
        else:
          return render_template('login.html', error={'login': 'Incorrect username or password'})
    except Exception as error:
      print(error)
      con.rollback()
      return render_template('login.html', error={'login': 'Some error occured'})
  if request.method == 'GET':
    return render_template('login.html', error={})
  else:
    abort(400)
@app.route('/register', methods=['POST'])
def register():
  username = request.form['name']
  password = request.form['password']
  password_repeat = request.form['password-repeat']
  if username == "" or password == "" or password_repeat == "":
    return render_template('login.html', error={'register': 'Please fill all fields'})
  if password != password_repeat:
    return render_template('login.html', error={'register': 'Passwords must match'})
  try:
    hash = bcrypt.generate_password_hash(password).decode("utf-8")
    with sqlite3.connect("./db/database.db") as con:
      cur = con.cursor()
      cur.execute('INSERT INTO "users" ("name", "password_hash") VALUES(?, ?)', (username, hash))
      con.commit()
      session['name'] = username
  except Exception as error:
    print(error)
    con.rollback()
    return render_template('login.html', error={'register': 'Some error occured'})
  return redirect('/', code=302)

@app.route('/', methods=['GET', 'POST'])
def home():
  history = []
  try:
    with sqlite3.connect("./db/database.db") as con:
      cur = con.cursor()
      cur.execute('SELECT * FROM "users" LEFT JOIN "results" ON users.name = results.username WHERE name=?', (session['name'],))
      rv = cur.fetchall()
      con.commit()
      print(rv)
      for row in rv:
        if row[6] != None:
          with open(row[6]) as f:
            history.append(f.read())
  except Exception as error:
    print(error)
    con.rollback()
    return render_template('login.html', error={'login': 'Some error occured'})
  if request.method == 'GET':
    return render_template('index.html', history=history)
  if request.method == 'POST':
    file = request.files['file']
    file_name = f"./uploaded/{time.time()}_{secure_filename(file.filename)}"
    if not os.path.exists('./uploaded'):
      os.makedirs('./uploaded')
    file.save(file_name)
    text = process_file(file_name)
    return render_template('index.html', text=text, history=history)
  else:
    abort(400)


if __name__ == "__main__":
  init_db()
  app.run(debug=False)
