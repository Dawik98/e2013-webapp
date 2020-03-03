from flask import Flask, render_template, request

import sqlite3
from flask import g

app = Flask(__name__)

DATABASE = './app/database.db' # on local machine
#DATABASE = './database.db' # on docker

def get_db():
  db = getattr(g, '_database', None)
  if db is None:
    db = g._database = sqlite3.connect(DATABASE)
    print("Successfully Connected to SQLite")
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
  c.close() #close db
  val = var['value']

  return render_template('index.html', val=val)

@app.route('/dataSave', methods=['POST'])
def dataSave ():
  # print("At data save")
  content = request.get_json()
  print (content)

  time = content['Time']
  device_type = content['Messurment']
  device_id = content['Sensors']
  value = float(content['Value'])
  print(type(value))

  db = get_db()
  c = db.cursor()
  c.execute("INSERT INTO messurments(timestamp, device_type, device_id, value) VALUES(?, ?, ?, ?);", (time, device_type, device_id, value))
  db.commit()
  db.close() #close db



  return 'JSON recieved'

if __name__ == '__main__':
  app.run()
