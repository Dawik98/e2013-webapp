from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo


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