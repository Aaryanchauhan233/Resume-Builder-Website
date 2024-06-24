import os
class Config:
    SECRET_KEY = os.urandom(24)
    SQLALCHEMY_DATABASE_URI = 'mysql://root:harshrajput147@localhost/site_db'
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'hr168074@gmail.com'
    MAIL_PASSWORD = '*************'  

