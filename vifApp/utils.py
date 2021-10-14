from django.core.mail import EmailMessage
import string
import secrets
import boto3
from botocore.exceptions import ClientError

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


    @staticmethod
    def create_presigned_url(bucket_name, region_name, object_name, expiration=60):
        s3_client = boto3.client('s3', region_name=region_name)
        try:
            response = s3_client.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': object_name}, ExpiresIn=expiration)
        except ClientError as e:
            return None
        return response

        
