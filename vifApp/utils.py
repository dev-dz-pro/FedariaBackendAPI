from django.core.mail import EmailMessage
import random


class VifUtils:
    @staticmethod
    def send_email(data):
        email = EmailMessage(subject=data["email_subject"], body=data["email_body"], to=[data["to_email"]])
        email.send()
    
'''
# @staticmethod
# def generate_username(name):
#     return name + str(random.randint(10000, 99999))
'''


        
