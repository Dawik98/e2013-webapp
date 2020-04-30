import flask
from flask import Flask, render_template, request, g, url_for, flash, redirect, Blueprint, send_file
from flask_mqtt import Mqtt
#from forms import RegistrationForm, LoginForm
#from getUsers import get_users
from flask_login import current_user, logout_user, login_required, login_user
from cosmosDB import read_from_db, write_to_db
from mqttCommunication import claimMeterdata

from login import User, login_manager, send_email_newUser, RegistrationForm, LoginForm, get_users

from graphData import print_historiskData
from dashApps.innstillinger import get_sløyfer
import pandas as pd
import xlsxwriter
from werkzeug.security import check_password_hash, generate_password_hash
import json, os, io


app=Blueprint('app', __name__)

#Definerer adresse til index side, og beskriver hvordan den skal se ut
@app.route('/')
def Index():
    return render_template('index.html', title="Index")

#Definerer adresse til index side, og beskriver hvordan den skal se ut
@app.route('/login', methods=['GET', 'POST'])
def login():
    #Dersom brukeren allerede er innlogget, styrer han videre til dashboard 
    if current_user.is_authenticated:
        print("authenticated")
        return redirect("/home/")
    #Henter in loginn klassen
    form = LoginForm()
    if form.validate_on_submit():
        from main import usersFile
        #henter brukere fra databasen og skriver dem til fil som brukes av "login manageren"
        users=get_users()
        with open(usersFile,'r+') as json_file:
            json_file.seek(0)
            json.dump(users, json_file)
        #Sjekker om brukeren er gyldig
        email = request.form.get('email')
        if users[email]['type'] == 'adminUser':
            if check_password_hash((users[email]["password"]), form.password.data):
                user = User()
                user.id = email
                print("Authenitcating user")
                #login_user(user)
                login_user(user, remember=form.remember.data)
                return redirect("/hjem/")
            else:
                flash('Login Unsuccessful. Please check username and password', 'danger')
        else:
            flash('Login Unsuccessful. Account awaits approval!', 'danger')
    return render_template('login.html', title="Login", form=form)

#Brukes til å logge ut brukere, blir automatisk videresendt til innlognings side
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

#Registrerings side 
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect("/hjem/")
    #Henter registrerings klassen til skjema
    form = RegistrationForm()
    #Sjekker om inputs er på riktig format, og om passord stemmer
    if form.validate_on_submit():
        NewUser={"type":"NotApproved", "username":form.username.data, "email":form.email.data, "password":generate_password_hash(form.password.data)}
        write_to_db('validUsers', NewUser)
        #Sender mail til Admins for å eventuellt godkjenne ny bruker
        send_email_newUser(form.email.data)
        #Dersom vellyket sendes videre til login
        flash(f'Account created for {form.username.data}. Waiting for approval!', 'success')
        return redirect("/login")
    #Ved feil, tilbake til registrering
    return render_template('register.html', title="Register", form=form)

#Laste ned data til excel
@login_required
@app.route('/excel-download/')
def download_excel():
    #Henter informasjon som ble lagt til URL-en
    value = flask.request.args.get('value')
    value = value.split('/')
    sløyfe_valg= value[0]
    start_date = value[1]
    end_date = value[2]
    #Formaterer filnavn etter sløyfevalg og dato på målingene
    filename = 'historisk_data/' + sløyfe_valg + '/' + start_date + '_to_' + end_date + '.xlsx'
    #returnerer historisk data som pandas dataframe
    df = print_historiskData(sløyfe_valg, start_date, end_date)
    #Convert DF
    strIO = io.BytesIO()
    excel_writer = pd.ExcelWriter(strIO, engine="xlsxwriter")
    df.to_excel(excel_writer, sheet_name="sheet1")
    excel_writer.save()
    excel_data = strIO.getvalue()
    strIO.seek(0)

    return send_file(strIO,
                    attachment_filename="{}".format(filename),
                    as_attachment=True)
