import flask
from flask import Flask, render_template, request, g, url_for, flash, redirect, Blueprint
from flask_mqtt import Mqtt
from forms import RegistrationForm, LoginForm
from getUsers import get_users
from flask_login import login_user, current_user, UserMixin, logout_user, login_required
from cosmosDB import read_from_db
from mqttCommunication import claimMeterdata


    

import json, os, io
app=Blueprint('app', __name__)

class User(UserMixin):
    pass

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        print("authenticated?")
        return redirect("/")
    form = LoginForm()
    if form.validate_on_submit():
        print(users[form.email.data]["password"])
        email = request.form.get('email')
        if form.password.data == users[form.email.data]["password"]:
            user = User()
            user.id = email
            print("Authenitcating user")
            login_user(user)
            #login_user(user, remember=form.remember.data)
            return redirect("/")
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
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
@login_required
def register():
    if current_user.is_authenticated:
        return redirect("/")
    form = RegistrationForm()
    if form.validate_on_submit():
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect("/login")
    return render_template('register.html', title="Register", form=form)
