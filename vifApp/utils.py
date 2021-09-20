from django.core.mail import EmailMessage

class VifUtils:
    @staticmethod
    def send_email(data):
        print(data)
        email = EmailMessage(subject=data["email_subject"], body=data["email_body"], to=[data["to_email"]])
        email.send() # fail_silently=True
