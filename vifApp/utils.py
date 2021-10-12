from django.core.mail import EmailMessage
import string
import secrets
from django.core.exceptions import ValidationError

class VifUtils:
    @staticmethod
    def send_email(data):
        email = EmailMessage(subject=data["email_subject"], body=data["email_body"], to=[data["to_email"]])
        email.send()
    
    @staticmethod
    def generate_username(name):
        ran_str = ''.join(secrets.choice(string.ascii_uppercase +
                                        string.digits+string.ascii_lowercase)
                                        for _ in range(9))
        return name + "_" + str(ran_str)

        
