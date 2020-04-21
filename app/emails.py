from flask_mail import Mail, Message

# administrator list
ADMINS = ['kristobh@stud.ntnu.no', 'omgoa@stud.ntnu.no', 'dawidk@stud.ntnu.no', 'kjetilhv@stud.ntnu.no']
def connect_mail(server):
    global mail
    mail=Mail(server)

def send_email_newUser():
    subject="New user created!"
    msg = Message(subject, recipients=ADMINS)
    """
    msg.body = text_body
    msg.html = html_body
    """
    mail.send(msg)

"""
def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)
"""