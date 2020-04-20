# email server
MAIL_SERVER = 'smtp.googlemail.com'
MAIL_PORT = 465
MAIL_USE_TLS = False
MAIL_USE_SSL = True
#Legger brukernavn og passord inn i eviorment variabel. Det er tryggere enn å legge de direkte i source file
MAIL_USERNAME = os.environ.get('bachelorgrupee2013@gmail.com')
MAIL_PASSWORD = os.environ.get('E2013LoRa')

# administrator list
ADMINS = ['kristobh@stud.ntnu.no']
