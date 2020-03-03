from flask import Flask, render_template

import sqlite3
from flask import g

app = Flask(__name__)

DATABASE = './app/database.db'

def get_db():
  db = getattr(g, '_database', None)
  if db is None:
    db = g._database = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
  return db

@app.teardown_appcontext
def close_connection(exception):
  db = getattr(g, '_database', None)
  if db is not None:
    db.close()

@app.route('/')
def hello_world():

  c = get_db().cursor()
  c.execute("SELECT * FROM messurments ORDER BY ROWID DESC LIMIT 1")
  var = c.fetchone()
  name = var['value']

  return render_template('index.html', name=name)

if __name__ == '__main__':
  app.run()
