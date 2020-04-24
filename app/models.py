from flask_login import UserMixin, LoginManager
from getUsers import get_users
import json

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

#Tok bort dette, åsså virket det. Vet ikke hvorfor...    
"""
@login_manager.request_loader
def request_loader(request):
    users=get_users()
    email = request.form.get('email')
    if email not in users:
        return
    user = User()
    user.id = email

    # DO NOT ever store passwords in plaintext and always compare password
    # hashes using constant-time comparison!
    if request.form['password'] != users[email]['password']:
        return 
    return user
"""