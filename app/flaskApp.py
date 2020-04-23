import flask
from flask import Flask, render_template, request, g, url_for, flash, redirect, Blueprint, send_file
from flask_mqtt import Mqtt
from forms import RegistrationForm, LoginForm
from getUsers import get_users
from flask_login import current_user, logout_user, login_required, login_user
from cosmosDB import read_from_db, write_to_db
from mqttCommunication import claimMeterdata
from models import User, login_manager
from emails import send_email_newUser
from historie_data import update_historiskData
from dashApps.innstillinger import get_sløyfer
import pandas as pd
import xlsxwriter
from werkzeug.security import check_password_hash, generate_password_hash
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
                return redirect("/hjem/")
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

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect("/hjem/")
    form = RegistrationForm()
    if form.validate_on_submit():
        NewUser={"type":"NotApproved", "username":form.username.data, "email":form.email.data, "password":generate_password_hash(form.password.data)}
        write_to_db('validUsers', NewUser)
        #Sender mail til Admins for å eventuellt godkjenne ny bruker
        send_email_newUser(form.email.data)

        flash(f'Account created for {form.username.data}. Waiting for approval!', 'success')
        return redirect("/login")
    return render_template('register.html', title="Register", form=form)

#Laste ned data til excel
@login_required
@app.route('/excel-download/')
def download_excel():
    
    value = flask.request.args.get('value')
    value = value.split('/')
    sløyfe_valg= value[0]
    start_date = value[1]
    end_date = value[2]

    filename = 'historisk_data/' + sløyfe_valg + '/' + start_date + '_to_' + end_date + '.xlsx'

    sløyfer=get_sløyfer()
    historiskData = update_historiskData(sløyfe_valg)

    d = {'Time recived, temp': historiskData["Temperatur-Sensor"]["timeReceived"],
        'Temperatur [°C]': historiskData["Temperatur-Sensor"]["temperature"],
        'Time recived, rele': historiskData["Power-Switch"]["timeReceived"],
        'activePower [W]': historiskData["Power-Switch"]["activePower"],
        'reactivePower [VAr]': historiskData["Power-Switch"]["reactivePower"],
        'apparentPower [VA]': historiskData["Power-Switch"]["apparentPower"],
        'activeEnergy [kWh]': historiskData["Power-Switch"]["activeEnergy"],
        'reactiveEnergy [kVAh]': historiskData["Power-Switch"]["reactiveEnergy"],
        'apparentEnergy [VArh]': historiskData["Power-Switch"]["apparentEnergy"],
        'voltage [V]': historiskData["Power-Switch"]["voltage"],
        'current [mA]': historiskData["Power-Switch"]["current"],
        'frequency [f]': historiskData["Power-Switch"]["frequency"],
        'runTime [s]': historiskData["Power-Switch"]["runTime"],
         }
    #Unngår feil på grunn av ulike lengder på listene.
    df = pd.DataFrame.from_dict(data=d, orient='index')
    df=df.transpose()

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
