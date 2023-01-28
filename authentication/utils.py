from datetime import date, datetime
from django.core.mail import EmailMessage
from django.shortcuts import get_object_or_404
from rest_framework import renderers
from django.utils.text import slugify
from authentication.models import *
from base64 import b64encode
from decouple import config
import threading
import random
import string
import json
import re
import os

class EmailThread(threading.Thread):

    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        self.email.send()


class Util:
    @staticmethod
    def send_email(data):
        email = EmailMessage(
            subject=data['email_subject'], body=data['email_body'], to=[data['to_email']])
        EmailThread(email).start()


def send_email_otp(email):
    """
    This is an helper function to send otp to session stored phones or 
    passed email as argument.
    """

    if email:
        key = otp_generator()
        email = email
        otp_key = str(key)
        data = {'email_body': 'Please use this code for your CocoBytes Chocolate account verification ' + otp_key, 'to_email': email, 'email_subject': 'Email Verification'}
        Util.send_email(data)

        # link = f'https://2factor.in/API/R1/?module=TRANS_SMS&apikey=f36765d2-5dfe-11ec-b710-0200cd936042&to={phone_number}&from=wisfrg&templatename=wisfrags&var1={otp_key}'

        # result = requests.get(link, verify=False)
        # print(result)

        return otp_key
    else:
        return False


def send_create_password_link(phone_number):
    """
    This is an helper function to send link to user to create password phone number as argument.
    """
    if phone_number:
        phone_number = str(phone_number)
        password_link = config['CREATE_PASSWORD_LINK']
        user = get_object_or_404(User, phone_number__iexact=phone_number)
        if user.first_name:
            first_name = user.first_name
        else:
            first_name = phone_number

        # link = f'https://2factor.in/API/R1/?module=TRANS_SMS&apikey=f36765d2-5dfe-11ec-b710-0200cd936042&to={phone_number}&from=wisfgs&templatename=Wisfrags&var1={first_name}&var2={password_link}'

        # result = requests.get(link, verify=False)
        # print(result)

        return password_link
    else:
        return False


def send_otp(phone_number):
    """
    This is an helper function to send otp to session stored phones or 
    passed phone number as argument.
    """

    if phone_number:
        key = otp_generator()
        phone_number = str(phone_number)
        otp_key = str(key)

        # link = f'https://2factor.in/API/R1/?module=TRANS_SMS&apikey=f36765d2-5dfe-11ec-b710-0200cd936042&to={phone_number}&from=wisfrg&templatename=wisfrags&var1={otp_key}'

        # result = requests.get(link, verify=False)
        # print(result)

        return otp_key
    else:
        return False

def send_otp_forgot(phone):
    """
    This is an helper function to forgot password otp to session stored phones or 
    passed phone number as argument.
    """
    if phone:
        key = otp_generator()
        phone = str(phone)
        otp_key = str(key)
        # user = get_object_or_404(User, phone_number__iexact=phone)
        # if user.first_name:
        #     first_name = user.first_name
        # else:
        #     first_name = phone
        # link = f'https://2factor.in/API/R1/?module=TRANS_SMS&apikey=f36765d2-5dfe-11ec-b710-0200cd936042&to={phone_number}&from=wisfgs&templatename=Wisfrags&var1={first_name}&var2={otp_key}'

        # result = requests.get(link, verify=False)
        # print(result)

        return otp_key
    else:
        return False


def random_string_generator(size=10, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def unique_otp_generator(instance):

    key = random.randint(0, 999999)
    print(key)

    Klass = instance.__class__
    qs_exists = Klass.objects.filter(key=key).exists()
    if qs_exists:
        return unique_otp_generator(instance)
    return key


def otp_generator():
    otp = str(random.randint(1000,9999))
    return otp


Dont_use = ['create']


def unique_slug_generator(instance, new_slug=None):
    if new_slug is not None:
        slug = new_slug
    else:
        slug = slugify(instance.title)
    if slug in Dont_use:
       new_slug = "{slug} - {randstr}".format(
           slug=slug,
           randstr=random_string_generator(size=4)
       )
       return unique_slug_generator(instance, new_slug=new_slug)

    klass = instance.__class__
    qs_exists = klass.objects.filter(slug=slug).exists()
    if qs_exists:
        new_slug = "{slug} - {randstr}".format(
            slug=slug,
            randstr=random_string_generator(size=4)
        )
        return unique_slug_generator(instance, new_slug=new_slug)
    return slug


def phone_validator(phone_number):
    """
    Returns true if phone number is correct else false
    """
    regix = r'^\+?1?\d{10}$'
    com = re.compile(regix)
    find = len(com.findall(phone_number))
    if find == 1:
        return True
    else:
        return False


def password_generator(length):
    """
    Generate fake password of passed length.
    """
    string = "abcdefghijklmnopqrstuvwxyz01234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()?"
    password = "".join(random.sample(string, length))
    return password


def unique_hex_generator(phone_number: str, password: str):
    string = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%^&*'
    salt_int = str(random.randint(1, 999999999999))
    salt_str = "".join(
        [i for i in random.sample(string, random.randint(0, 70))])
    byte_like = bytes(
        str(salt_int+salt_str+str(phone_number)+password).encode('utf-8'))
    return b64encode(byte_like)


class UserRenderer(renderers.JSONRenderer):
    charset = 'utf-8'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = ''
        if 'ErrorDetail' in str(data):
            response = json.dumps({'errors': data})
        else:
            response = json.dumps({'data': data})
        return response


class EmailThread(threading.Thread):

    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        self.email.send()


class Util:
    @staticmethod
    def send_email(data):
        email = EmailMessage(
            subject=data['email_subject'], body=data['email_body'], to=[data['to_email']])
        EmailThread(email).start()


def upload_image_path_profile(instance, filename):
    new_filename = random.randint(1, 9996666666)
    name, ext = get_filename_ext(filename)
    final_filename = '{new_filename}{ext}'.format(
        new_filename=new_filename, ext=ext)
    return "profiles/{final_filename}".format(new_filename=new_filename, final_filename=final_filename)


def get_filename_ext(filepath):
    base_name = os.path.basename(filepath)
    name, ext = os.path.splitext(base_name)
    return name, ext

def calculate_age(dob):
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

def calculate_age_with_string(birthdate_string):
    birthdate = datetime.strptime(birthdate_string, "%Y-%m-%dT%H:%M:%SZ")
    today = datetime.today()
    return today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
