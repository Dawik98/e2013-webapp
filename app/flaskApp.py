from flask import Flask, render_template, request, g, url_for, flash, redirect, Blueprint
from flask_mqtt import Mqtt
from forms import RegistrationForm, LoginForm

from cosmosDB import read_from_db

import json
import os
import io

from mqtt import mqtt, connect_to_db

app=Blueprint('app', __name__)

@app.route('/claimMeterdata')
def claimMeterdata():
    mqtt.publish('powerSwitch', bytes([4, 2, 0]))

@app.route('/activateHeatTrace')
def activateHeatTrace():
    mqtt.publish('powerSwitch', bytes([4, 0, 0, 0, 0, 0, 1, 0, 0, 0]))

@app.route('/deactivateHeatTrace')
def deactivateHeatTrace():
    mqtt.publish('powerSwitch', bytes([4, 0, 1, 0, 0, 0, 0, 0, 0, 0]))


# main web page
@app.route('/')
@app.route('/Home')
def Home():

    # print(get_containers()) 

    #query data from database
    query = "SELECT * FROM heatTrace1 WHERE heatTrace1.deviceType = 'tempSensor' ORDER BY heatTrace1.timeReceived DESC"
    container_name = "heatTrace1"

    items = read_from_db(container_name, query)

    val = items[0]['temperature']

    return render_template('index.html',målinger=målinger, val=val)

@app.route('/SensorData')
def SensorData():
    return render_template('SensorData.html', title='Målinger')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('Home'))
    return render_template('register.html', title="Register", form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if form.email.data =='admin@blog.com' and form.password.data == 'password':
            flash('You have been logged in!','success')
            return redirect(url_for('Home'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', title="Login", form=form)


 
