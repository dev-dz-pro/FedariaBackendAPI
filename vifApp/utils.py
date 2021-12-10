from django.core.mail import EmailMessage
import string
import secrets
import boto3
import time
from botocore.exceptions import ClientError
from django.conf import settings
from urllib.parse import urlparse
import hashlib


class VifUtils:
    def create_presigned_url(self, bucket_name, region_name, object_name, expiration=60):
        s3_client = boto3.client('s3', region_name=region_name)
        try:
            response = s3_client.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': object_name}, ExpiresIn=expiration)
        except ClientError as e:
            return None
        return response


    def aws_upload_file(self, user, file, for_profile=True):
        if for_profile:
            if user.profile_image.startswith("https://vifbox-backend.s3.amazonaws.com"):  # this condition for upqding profile image qnd not creqting nez one
                file_aws_name = urlparse(user.profile_image).path[1:]
            else:
                timestr = time.strftime("%Y%m%d%H%M%S")
                ext = "."+file.name.split(".")[-1]
                file_aws_name = "profile_pics/img_"+timestr+ext
        else:
            emailid = user.email + str(user.id)
            dir = hashlib.sha256(emailid.encode()).hexdigest()
            timestr = time.strftime("%Y%m%d%H%M%S")
            file_aws_name = f"projects_files/{dir}/"+timestr+"_"+file.name
        boto3.client('s3', region_name=settings.REGION_NAME).upload_fileobj(file, settings.BUCKET_NAME, file_aws_name)
        img_url = self.create_presigned_url(settings.BUCKET_NAME, settings.REGION_NAME, file_aws_name, expiration=600000)
        return img_url


    def delete_from_s3(self, user, file_name):
        try:
            emailid = user.email + str(user.id)
            dir = hashlib.sha256(emailid.encode()).hexdigest()
            if file_name.startswith(f"projects_files/{dir}/"):
                s3 = boto3.client("s3", region_name=settings.REGION_NAME)
                s3.delete_object(Bucket=settings.BUCKET_NAME, Key=file_name)
                return True
            else:
                return False
        except Exception:
            return False


    @staticmethod
    def send_email(data):
        email = EmailMessage(subject=data["email_subject"], body=data["email_body"], to=data["to_email"])
        email.send()
    

    @staticmethod
    def generate_username(name):
        ran_str = ''.join(secrets.choice(string.ascii_uppercase +
                                        string.digits+string.ascii_lowercase)
                                        for _ in range(9))
        return name + "_" + str(ran_str)

        
