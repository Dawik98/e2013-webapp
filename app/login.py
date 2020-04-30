from cosmosDB import read_from_db

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo

from flask_login import UserMixin, LoginManager
#from cosmosDB import get_users
import json

from flask_mail import Mail, Message



#Henter brukere fra databasen på ønsket format der hver email har et dictonary med nødvendig informasjon
def get_users():
    query = "SELECT * FROM validUsers ORDER BY validUsers._ts DESC"
    container_name = 'validUsers'
    #print(query)
    items = read_from_db(container_name, query)
    #print (items)

    users={}
    for i in items:
        users[i['email']]={ "username":i['username'],
                                "type":i['type'],
                                "password":i['password'],
                                "id":i['id']
                            }
    return users

#Definerer loginmanageren som holder styr på brukere
login_manager=LoginManager()

#Importerer nødvendige atributter til bruker klassen
class User(UserMixin):
        pass

#Denne funksjonen kjøres hele tiden av login managereren for å sjekke om brukerene har logget inn osv
@login_manager.user_loader
def user_loader(email):
    from main import usersFile
    users={}
    #Denne kjøres hele tiden, laster derfor brukere inn fra fil, i stedet for database query.
    #Slik programmet kjører bedre
    with open(usersFile) as json_file:
        users = json.load(json_file)
    if email not in users:
        print("Email not in users")
        return
    user = User()
    user.id = email
    return user


#klasser som brukes til innloggnings og regstrings- skjemaer
class RegistrationForm(FlaskForm):
    username = StringField('Brukernavn',
                            validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('E-post',
                         validators=[DataRequired(), Email()])
    password = PasswordField('Passord',
                            validators=[DataRequired()])
    confirm_password = PasswordField('Bekreft passord',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Send inn søknad!')

class LoginForm(FlaskForm):
    email = StringField('E-post',
                         validators=[DataRequired(), Email()])
    password = PasswordField('Passord',
                            validators=[DataRequired()])
    remember = BooleanField('Husk meg')
    submit = SubmitField('Logg inn')


# administrator list
ADMINS = ['kristobh@stud.ntnu.no', 'omgoa@stud.ntnu.no', 'dawidk@stud.ntnu.no', 'kjetilhv@stud.ntnu.no']
def connect_mail(server):
    global mail
    mail=Mail(server)
# Funksjon som kjøres hver gang ny bruker opprettes. Varlser ADMINS på email om nødvendig godkjenning
def send_email_newUser(user_email):
    subject="New user created!"
    msg = Message(subject, recipients=ADMINS)
    msg.body = "En konto er registert for bruker: {}".format(user_email)
    mail.send(msg)



