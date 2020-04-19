from flask_login import UserMixin, LoginManager
from getUsers import get_users

login_manager=LoginManager()

class User(UserMixin):
        pass

@login_manager.user_loader
def user_loader(email):
    users=get_users()
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