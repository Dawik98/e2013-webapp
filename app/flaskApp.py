import flask
from flask import Flask, render_template, request, g, url_for, flash, redirect, Blueprint
from flask_mqtt import Mqtt
from forms import RegistrationForm, LoginForm
from getUsers import get_users
from flask_login import current_user, logout_user, login_required, login_user
from cosmosDB import read_from_db, write_to_db
from mqttCommunication import claimMeterdata
from models import User, login_manager
from emails import send_email_newUser
from werkzeug.security import check_password_hash, generate_password_hash
import json
    

import json, os, io


app=Blueprint('app', __name__)

@app.route('/')
def Index():
    return render_template('index.html', title="Index")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        print("authenticated")
        return redirect("/home/")
    form = LoginForm()
    if form.validate_on_submit():
        from main import usersFile
        users=get_users()
        with open(usersFile,'r+') as json_file:
            json_file.seek(0)
            json.dump(users, json_file)

        email = request.form.get('email')
        if users[email]['type'] == 'adminUser':
            if check_password_hash((users[email]["password"]), form.password.data):
                user = User()
                user.id = email
                print("Authenitcating user")
                #login_user(user)
                login_user(user, remember=form.remember.data)
                return redirect("/home/")
            else:
                flash('Login Unsuccessful. Please check username and password', 'danger')
        else:
            flash('Login Unsuccessful. Account awaits approval!', 'danger')
    return render_template('login.html', title="Login", form=form)
    
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

@app.route('/claimMeterdata')
def runClaimDataFunction():
    return claimMeterdata('heatTrace1')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect("/home/")
    form = RegistrationForm()
    if form.validate_on_submit():
        NewUser={"type":"NotApproved", "username":form.username.data, "email":form.email.data, "password":generate_password_hash(form.password.data)}
        write_to_db('validUsers', NewUser)
        #Sender mail til Admins for å eventuellt godkjenne ny bruker
        #from main import mail
        send_email_newUser()

        flash(f'Account created for {form.username.data}. Waiting for approval!', 'success')
        return redirect("/login")
    return render_template('register.html', title="Register", form=form)
