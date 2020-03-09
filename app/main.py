from flask import Flask, render_template, request, g
from flask_mqtt import Mqtt

import sqlite3
import json

app = Flask(__name__)

# setup mqtt
app.config['MQTT_BROKER_URL'] = '13.74.42.218'
app.config['MQTT_BROKER_PORT'] = 9990
app.config['MQTT_USERNAME'] = 'e2013'
app.config['MQTT_PASSWORD'] = 'potet'
app.config['MQTT_REFRESH_TIME'] = 1.0  # refresh time in seconds
mqtt = Mqtt(app)

#DATABASE = './app/database.db' # on local machine
DATABASE = './database.db' # on docker

# connect to database
def get_db():
  db = getattr(g, '_database', None)
  if db is None:
    db = g._database = sqlite3.connect(DATABASE)
    print("Successfully Connected to SQLite")
    db.row_factory = sqlite3.Row
  return db

# close database when disconecting? 
@app.teardown_appcontext
def close_connection(exception):
  db = getattr(g, '_database', None)
  if db is not None:
    db.close()

# run when connection with the broker
@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    mqtt.subscribe('test')
    print("Subscribed to test topic")

# run when new message is published to the subscribed topic
@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    data = dict(
        topic=message.topic,
        payload=json.loads(message.payload.decode()) # get payload and convert it to a dictionary
    )
    print(data)


# main web page
@app.route('/')
def hello_world():

  c = get_db().cursor()
  c.execute("SELECT * FROM messurments ORDER BY ROWID DESC LIMIT 1")
  var = c.fetchone()
  c.close() #close db
  val = var['value']

  return render_template('index.html', val=val)

# save data to database
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
