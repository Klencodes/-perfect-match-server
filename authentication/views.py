from django.forms import ValidationError
from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView, UpdateAPIView, DestroyAPIView
from rest_framework.parsers import FileUploadParser
from rest_framework import generics, status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import get_object_or_404
from helpers.pagination import CustomPagination
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from datetime import datetime, timedelta
from rest_framework.views import APIView
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Q
from .serializers import *
from helpers.permission import *
from .models import *
from .utils import *

class UploadPhoto(CreateAPIView):
    parser_class = (FileUploadParser,)

    def post(self, request, *args, **kwargs):
        print(request.data, "PHOTO DATA")

        file_serializer = FileSerializer(data=request.data)
        if file_serializer.is_valid():
            file_serializer.save()
            return Response({"response": "SUCCESSFUL", "message": "Profile successfully uploaded", "results": file_serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SignUpAPI(APIView):
    '''
    This class view takes phone number and if it doesn't exists already then it sends otp for
    first coming phone numbers'''

    def post(self, request, *args, **kwargs):
        phone = request.data['phone_number']
        if phone:
            user = User.objects.filter(phone_number=phone)
            if user.exists():
                raise AuthenticationFailed({"response": "FAILED", "message": "Phone number already exists"})
                # logic to send the otp and store the phone number and that otp in table.
            else:
                # Create initial user account
                serializer = CreateUserSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                user = serializer.save()
                user_info = User.objects.get(phone_number=phone)
                # token, created = Token.objects.get_or_create(user=user_info)
                user_serializer = UserSerializer(user_info, context={"request": request})
                # user_serializer.auth_token = str(token)
                code = send_otp(phone)                
                if code:
                    count = 0                    
                    old = PhoneOTP.objects.filter(phone_number = phone)
                    if old.exists():
                        old = old.first()
                        count = old.count                     
                        old.count = count + 1
                        old.otp = str(code)
                        old.save() 
                    else:
                        code = send_otp(phone)                
                        count = count + 1
                        PhoneOTP.objects.create(phone_number=phone, otp=str(code), count=count)
                    if count >= 5:
                        raise AuthenticationFailed({"response": "FAILED", "message": "Maximum OTP limits reached. Kindly contact our customer care or try with different number"})
                else:
                    raise AuthenticationFailed({"response": "FAILED", "message": "OTP sending error. Please try after some time."})

                return Response({"response": "SUCCESSFUL", "message": "OTP has been sent successfully.", "results": user_serializer.data})
                
        else:
            raise AuthenticationFailed({"response": "FAILED", "message": "I haven't received any phone number. Please do a POST request."})

class ResendOTP(APIView):
    '''
    This class view takes phone number and if it doesn't exists already then it sends otp for
    first coming phone numbers'''
    def post(self, request):
        phone = request.data['phone_number']
        if phone:
            count = 0
            old = PhoneOTP.objects.filter(phone_number=phone)
            if old.exists():
                code = send_otp(phone)
                old = old.first()
                count = old.count                     
                old.count = count + 1
                old.otp = str(code)
                old.save() 
            else:
                # return Response({"response": "FAILED", "message": "User with " + phone +"  does not exist."})
                code = send_otp(phone)              
                count = count + 1
                PhoneOTP.objects.create(phone_number=phone, otp=str(code), count=count)
            if count >= 5:
                return Response({"response": "FAILED", "message": "Maximum OTP limits reached. Kindly contact our customer care or try with different number"})
            
            return Response({"response": "SUCCESSFUL", "message": "OTP has been successfully sent"})
        else:
            return Response({"response": "FAILED", "message": "OTP sending error. Please try after some time."})

class VerifyPhoneNumber(APIView):
    '''
    If you have received otp, post a request with phone number and that otp and you will be redirected to set the password
    
    '''
    def post(self, request, *args, **kwargs):
        phone = request.data.get('phone_number', False)
        otp_sent = request.data.get('otp', False)
        if phone and otp_sent:
            old = PhoneOTP.objects.filter(phone_number__iexact=phone)
            if old.exists():
                old = old.first()
                otp_old = old.otp
                if str(otp_old) == str(otp_sent):
                    old.delete()
                    user_info = User.objects.get(phone_number=phone)
                    user_info.verified_phone = True
                    user_info.save()
                    token, created = Token.objects.get_or_create(user=user_info)
                    user_serializer = UserSerializer(user_info, context={"request": request})
                    user_data = user_serializer.data
                    user_data["auth_token"] = str(token)
                    return Response({"response": "SUCCESSFUL", "message": "Phone number verified successfully", "results": user_data})
                else:
                    return Response({"response": "FAILED", "message": "OTP incorrect, please try again"})
            else:
                return Response({"response": "FAILED", "message": "Phone number not recognised. Kindly request a new otp with "+ phone})
        else:
            return Response({"response": "FAILED", "message": "Either Phone number or otp field is empty"})

class CreateLegalName(CreateAPIView):
    '''
    create user full or legal name auth token is required
    
    '''
    permission_classes = [IsAuthenticated]

    def post(self, request, pk=None):
        user_data = request.data
        user = self.request.user
        user_info = User.objects.get(id=user.id)
        user_info.first_name = user_data['first_name']
        user_info.last_name = user_data['last_name']
        user_info.onboarding_percentage = user_data['onboarding_percentage']
        user_info.save()
        token, created = Token.objects.get_or_create(user=user_info)
        user_serializer = UserSerializer(user_info, context={"request": request})
        user_data = user_serializer.data
        user_data["auth_token"] = str(token)
        return Response({"response": "SUCCESSFUL", "message": "User Information successfully returned", "results": user_data}, status=status.HTTP_200_OK)

class UpdateProfilePhoto(CreateAPIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, pk=None):
        user_data = request.data
        user = self.request.user
        user_info = User.objects.get(id=user.id)
        user_info.profile_picture = user_data['profile_picture']
        user_info.onboarding_percentage = user_data['onboarding_percentage']
        user_info.save()
        token, created = Token.objects.get_or_create(user=user_info)
        user_serializer = UserSerializer(user_info, context={"request": request})
        user_data = user_serializer.data
        user_data["auth_token"] = str(token)
        return Response({"response": "SUCCESSFUL", "message": "User Information successfully returned", "results": user_data}, status=status.HTTP_200_OK)

class CreateBirthDate(CreateAPIView):
    '''
    create user date of birth auth token is required
    
    '''
    permission_classes = [IsAuthenticated]

    def post(self, request, pk=None):
        user = self.request.user
        user_info = User.objects.get(id=user.id)
        user_info.birth_date = request.data["birth_date"]
        user_info.onboarding_percentage = request.data["onboarding_percentage"]
        user_info.save()
        token, created = Token.objects.get_or_create(user=user_info)
        user_serializer = UserSerializer(user_info, context={"request": request})
        user_data = user_serializer.data
        user_data["auth_token"] = str(token)
        return Response({"response": "SUCCESSFUL", "message": "User Information successfully returned", "results": user_data}, status=status.HTTP_200_OK)

class CreateAddress(CreateAPIView):
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        print(request, "REQUEST")
        try:
            user = self.request.user
            user_info = User.objects.get(id=user.id)
            user_info.onboarding_percentage = request.data["onboarding_percentage"]
            user_info.save()

            if request.data["is_home_address"] == True:
                old_primary_addressess = Address.objects.all()
                for item in old_primary_addressess:
                    item.is_home_address = False
                    item.save()

            if request.data["is_billing_address"] == True:
                old_primary_addressess = Address.objects.all()
                for item in old_primary_addressess:
                    item.is_billing_address = False
                    item.save()

            serializer = AddressPostSerializer(data=request.data, context={"request": request})
            serializer.is_valid(raise_exception=True)
            serializer.save(user=self.request.user)
            token, created = Token.objects.get_or_create(user=user_info)
            user_serializer = UserSerializer(user_info, context={"request": request})
            user_data = user_serializer.data
            user_data["auth_token"] = str(token)
            return Response({ "response": "SUCCESSFUL", "message": "Address successfully added", "results": user_data})
        except:
            return Response(serializer.errors)

class SendReactivateOTP(APIView):
    '''
    This class view takes phone number and if it doesn't exists already then it sends otp for
    first coming phone numbers'''
    def post(self, request):
        phone = request.data['phone_number']
        if phone:
            count = 0
            old = User.objects.filter(phone_number=phone)
            if old.exists():
                otp_exist = PhoneOTP.objects.filter(phone_number=phone)
                if otp_exist.exists():
                    code = send_otp(phone)
                    otp_exist = otp_exist.first()
                    count = otp_exist.count                     
                    otp_exist.count = count + 1
                    otp_exist.otp = str(code)
                    otp_exist.save() 
                else:
                    code = send_otp(phone)              
                    count = count + 1
                    PhoneOTP.objects.create(phone_number=phone, otp=str(code), count=count)
                    return Response({"response": "SUCCESSFUL", "message": "OTP has been successfully sent"})
                
                if count >= 5:
                    return Response({"response": "FAILED", "message": "Maximum OTP limits reached. Kindly contact our customer care or try with different number"})
            else:
                print("USER DOES NOT EXIST")
                return Response({"response": "FAILED", "message": "User with " + phone +"  does not exist."})
            
        else:
            return Response({"response": "FAILED", "message": "OTP sending error. Please try after some time."})

class ReactivateAccount(APIView):
 
    def post(self, request, *args, **kwargs):
        phone = request.data.get('phone_number', False)
        otp_sent = request.data.get('otp', False)
        if phone and otp_sent:
            old = PhoneOTP.objects.filter(phone_number__iexact=phone)
            if old.exists():
                old = old.first()
                otp_old = old.otp
                if str(otp_old) == str(otp_sent):
                    old.delete()
                    user_info = User.objects.get(phone_number=phone)
                    user_info.deactivated = False
                    user_info.save()
                    token, created = Token.objects.get_or_create(user=user_info)
                    user_serializer = UserSerializer(user_info, context={"request": request})
                    user_data = user_serializer.data
                    user_data["auth_token"] = str(token)
                    return Response({"response": "SUCCESSFUL", "message": "Account successfully activated", "results": user_data})
                else:
                    return Response({"response": "FAILED", "message": "OTP incorrect, please try again"})
            else:
                return Response({"response": "FAILED", "message": "Phone number not recognised. Kindly request a new otp with "+ phone})
        else:
            return Response({"response": "FAILED", "message": "Either Phone number or otp field is empty"})

class SignInAPI(generics.GenericAPIView):
    def post(self, request, *args, **kwargs):
        serializer = SignInUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        user = User.objects.get(phone_number=request.data['phone_number'])
        user.last_login = timezone.now()
        token, created = Token.objects.get_or_create(user=user)
        user.is_loggedin = True
        if user.last_login is None:
            user.first_login = True
            user.save()
        elif user.first_login:
            user.first_login = False
            user.save()
        user.save()
        user_serializer = UserSerializer(user, context={"request": request})
        user_data = user_serializer.data
        user_data["auth_token"] = str(token)
        return Response({"results": user_data, "message": "User logged in successfully", "response": "SUCCESSFUL"}, status=status.HTTP_200_OK)

class CreatePreferMatch(CreateAPIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, pk=None):
        user_data = request.data
        user = self.request.user
        user_info = User.objects.get(id=user.id)
        user_info.gender = user_data['gender']
        user_info.prefered_gender = user_data['prefered_gender']
        user_info.onboarding_percentage = user_data['onboarding_percentage']
        user_info.save()
        token, created = Token.objects.get_or_create(user=user_info)
        user_serializer = UserSerializer(user_info, context={"request": request})
        user_data = user_serializer.data
        user_data["auth_token"] = str(token)
        return Response({"response": "SUCCESSFUL", "message": "Prefered gender successfully set", "results": user_data}, status=status.HTTP_200_OK)

class AllowPushNotification(CreateAPIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, pk=None):
        user_data = request.data
        user = self.request.user
        user_info = User.objects.get(id=user.id)
        user_info.allow_push_notification = user_data['allow_push_notification']
        user_info.onboarding_percentage = user_data['onboarding_percentage']
        user_info.save()
        token, created = Token.objects.get_or_create(user=user_info)
        user_serializer = UserSerializer(user_info, context={"request": request})
        user_data = user_serializer.data
        user_data["auth_token"] = str(token)
        return Response({"response": "SUCCESSFUL", "message": "Prefered gender successfully set", "results": user_data}, status=status.HTTP_200_OK)



'''
Admin endpoints
'''
class FetchAllUsers(ListAPIView):
    permission_classes = [IsAdmin]

    def list(self, request):
        users = User.objects.all()
        if len(users) > 0:
            paginator = CustomPagination()
            serializer = UserSerializer(
                users, many=True, context={"request": request})
            result_page = paginator.paginate_queryset(users, request)
            return paginator.get_paginated_response(serializer.data)
        else:
            return Response({"message": "No data found"})

class UpdateUser(UpdateAPIView):
    permission_classes = [IsAdmin]

    def put(self, request, pk=None):
        try:
            queryset = User.objects.all()
            user = get_object_or_404(pk=pk)
            serializer = UserSerializer(user, data=request.data, context={"request": request})
            serializer.is_valid()
            user.date_updated = timezone()
            serializer.save()
            return Response({"response": "SUCCESSFUL", "message": "User successfully update"})
        except:
            return Response(serializer.errors)

class FetchAddresses(ListAPIView):
    permission_classes = [IsAdmin]

    def list(self, request):
        addresses = Address.objects.all()
        if len(addresses) > 0:
            paginator = CustomPagination()
            serializer = AddressDetailSerializer(
                addresses, many=True, context={"request": request})
            result_page = paginator.paginate_queryset(addresses, request)
            return paginator.get_paginated_response(serializer.data)
        else:
            return Response({"message": "No data found"})

'''
Users endpoint
'''
class ProfileUploadView(CreateAPIView):
    # permission_classes = (IsAuthenticated,)
    parser_class = (FileUploadParser)

    def post(self, request, *args, **kwargs):
        profile_serializer = ProfileSerializer(
            data=request.data, context={'request': request})
        if profile_serializer.is_valid():
            profile_serializer.save()
            return Response({"results": profile_serializer.data, "response": "SUCCESSFUL", "message": "Image uploaded successfully"}, status=status.HTTP_201_CREATED)
        else:
            return Response(profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ListAddresses(ListAPIView):
    permission_classes = [IsAuthenticated]
    def list(self, request):
        user = self.request.user
        addresses = Address.objects.filter(user=user)
        if len(addresses) > 0:
            serializer = AddressDetailSerializer(addresses, many=True, context={"request": request})
            return Response({"respons": "SUCCESSFUL", "message": "User addresses successfully returned", "results": serializer.data})
        else:
            return Response({"response": "SUCCESSFUL", "message": "No data found"})

class UpdatePrimaryAddress(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        #Set all old addresses primary fields to False
        db_addressess = Address.objects.all()
        for item in db_addressess:
            item.primary = False
            item.save()
        #Now set new primary address     
        address = Address.objects.get(id=request.data['address_id'])
        address.primary = request.data['address_state']
        address.save()
        return Response({"response": "SUCCESSFUL", "message": "Shipping address successfully changed"}, status=status.HTTP_200_OK)

class UpdateAddress(UpdateAPIView):
    permission_classes = [IsAuthenticated]

    def update(self, request, pk=None):
        try:
            address = Address.objects.get(id=request.data['address_id'])
            serializer = AddressDetailSerializer(address, data=request.data, context={"request": request})
            serializer.is_valid(raise_exception=True)
            address.date_updated = timezone.now()
            serializer.save()
            return Response({'response': 'SUCCESSFUL', 'message': 'Address successfully updated'})
        except:
            return Response(serializer.errors)

class DeleteAddress(DestroyAPIView):
    permission_classes = (IsAuthenticated,)

    def destroy(self, pk=None):
        try:
            queryset = Address.objects.all()
            address = get_object_or_404(queryset, pk=pk).delete()
            return Response({'response': 'SUCCESSFUL', 'message': 'Address successfully deleted'})
        except:
            return Response({'message': 'Error occured during processing'})

class UserAPI(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class ManagerSignInAPI(generics.GenericAPIView):
    def post(self, request, *args, **kwargs):
        serializer = SignInManagerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        user = User.objects.get(email=request.data['email'])
        user.last_login = timezone.now()
        token, created = Token.objects.get_or_create(user=user)
        user.is_loggedin = True
        if user.last_login is None:
            user.first_login = True
            user.save()
        elif user.first_login:
            user.first_login = False
            user.save()
        user.save()
        user_data = {
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'gender': user.gender,
            'is_verified': user.is_verified,
            'user_type': user.user_type,
            'last_login': user.last_login,
            'image': user.image,
            'auth_provider': user.auth_provider,
            'auth_token': token.key,
            'is_loggedin': user.is_loggedin,
        }
        return Response({"results": user_data, "message": "User logged in successfully", "response": "SUCCESSFUL"}, status=status.HTTP_200_OK)


class ValidatePhoneForgot(APIView):
    '''
    Validate if account is there for a given phone number and then send otp for forgot password reset
    
    '''
    def post(self, request, *args, **kwargs):
        phone_number = request.data.get('phone_number')
        if phone_number:
            phone_number = str(phone_number)
            user = User.objects.filter(phone_number__iexact = phone_number)
            if user.exists():
                otp = send_otp_forgot(phone_number)
                if otp:
                    otp = str(otp)
                    count = 0
                    old = PhoneOTP.objects.filter(phone_number__iexact = phone_number)
                    if old.exists():
                        old = old.first()
                        k = old.count
                        if k >= 5:
                            return Response({"response" : "FAILED", "message": "Maximum otp limits reached. Kindly support our customer care or try with different number"})
                        old.count = k + 1
                        old.save()
                        return Response({"response": "SUCCESSFUL", "message": "OTP has been sent for password reset."})
                    else:
                        count = count + 1
                        PhoneOTP.objects.create(phone_number=phone_number, otp=otp, count=count, forgot=True,)
                        return Response({"response": "SUCCESSFUL", "message": "OTP has been sent for password reset"})
                else:
                    return Response({"response": "FAILED", "message" : "OTP sending error. Please try after some time"})
            else:
                return Response({"response" : "FAILED", "message": "Phone number not recognised. Kindly try a new account for this number"})
    
class ForgotValidateOTP(APIView):
    '''
    If you have received an otp, post a request with phone number and that otp and you will be redirected to reset  the forgotted password
    
    '''

    def post(self, request, *args, **kwargs):
        phone = request.data.get('phone_number', False)
        otp_sent = request.data.get('otp', False)

        if phone and otp_sent:
            old = PhoneOTP.objects.filter(phone_number__iexact=phone)
            if old.exists():
                old = old.first()
                if old.forgot == False:
                    return Response({"response": "FAILED", "message": "This phone number have not send valid otp for forgot password."})
                otp = old.otp
                if str(otp) == str(otp_sent):
                    old.forgot_logged = True
                    old.save()
                    return Response({"response": "SUCCESSFUL", "message": "OTP verified, kindly proceed to create new password"})
                else:
                    return Response({"response": "FAILED", "message": "OTP incorrect, please try again"})
            else:
                return Response({"response": "FAILED", "message": "Phone number not recognised. Kindly request a new otp with this number"})
        else:
            return Response({"response": "FAILED", "message": "Either phone number or otp field is empty"})

class ForgetPasswordChange(APIView):
    '''
    if forgot_logged is valid and account exists then only pass otp, phone number and password to reset the password. All three should match.APIView
    '''

    def post(self, request, *args, **kwargs):
        phone = request.data.get('phone_number', False)
        otp = request.data.get("otp", False)
        password = request.data.get('password', False)
        confirm_password = request.data.get('confirm_password', False)

        if phone and otp and password:
            if password != confirm_password:
                return Response({"message": "Password do not match"})
            old = PhoneOTP.objects.filter(Q(phone_number__iexact=phone) & Q(otp__iexact=otp))
            if old.exists():
                old = old.first()
                if old.forgot_logged:
                    # post_data = {'phone_number' : phone_number, 'password' : password, confirm_password: 'confirm_password'}
                    user = get_object_or_404(User, phone_number__iexact=phone)
                    serializer = ForgetPasswordSerializer(data=request.data)
                    serializer.is_valid(raise_exception=True)
                    if user:
                        user.set_password(serializer.data.get('password'))
                        user.active = True
                        user.save()
                        old.delete()
                        return Response({"response": "SUCCESSFUL", "message": "Password changed successfully. Please Login"})
                else:
                    return Response({"response": "FAILED", "message": "OTP Verification failed. Please try again in previous step"})
            else:
                return Response({"response": "FAILED", "message": "Phone number and otp are not matching or a new phone number has entered. Request a new otp in forgot password"})
        else:
            return Response({"response": "FAILED", "message": "Post request have parameters mising"})


class ChangePasswordAPI(generics.UpdateAPIView):
    """
    Change password endpoint view
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = ChangePasswordSerializer

    def get_object(self, queryset=None):
        """Returns current logged in user instance"""
        return self.request.user

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            if not self.object.check_password(serializer.data.get('current_password')):
                return Response({"response": "FAILED", "message": "Data does not match with our data"}, status=status.HTTP_400_BAD_REQUEST)
            if serializer.data.get('password') != serializer.data.get('confirm_password'):
                return Response({"response": "FAILED", "message": "Passwords does not match"}, status=status.HTTP_400_BAD_REQUEST)
            self.object.set_password(serializer.data.get('confirm_password'))
            self.object.password_changed = True
            self.object.save()
            return Response({"response": "SUCCESSFUL",  "message": "Password has been changed successfully.", }, status=status.HTTP_200_OK)
        return Response(serializer.error, status=status.HTTP_400_BAD_REQUEST)

class UserInfoDetails(RetrieveAPIView):
    def retrieve(self, request, pk=None):
        user = self.request.user
        userData = User.objects.get(id=user.id)
        # orders=User.objects.all().filter(user=self.request.user)
        serializer = UserSerializer(userData, context={"request": request})
        serializer_data = serializer.data

        address = Address.objects.filter(user=user)
        address_serializers = AddressSerializer(address, many=True)
        serializer_data["addresses"] = address_serializers.data

        # orderCount = Order.objects.filter(user=user).count()
        # deliveredOrderCount = Order.objects.filter(Q(user=user) & Q(order_status='DELIVERED')).count()
        # savedItems = SavedItem.objects.filter(user=user).count()

        # serializer_data["saved_items"] = savedItems
        # serializer_data["order_count"] = orderCount
        # serializer_data["delivered_order_count"] = deliveredOrderCount

        return Response({"response": "SUCCESSFUL", "message": "User Information successfully returned", "results": serializer_data}, status=status.HTTP_200_OK)

class UpdateUserProfile(UpdateAPIView):
    """
    Change user first or last name endpoint view
    """
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        req_user = self.request.user
        db_user = User.objects.get(id=req_user.id)
        if db_user:
            db_user.first_name = request.data['first_name']
            db_user.last_name = request.data['last_name']
            db_user.phone_number = request.data['phone_number']
            db_user.save()
            return Response({"response": "SUCCESSFUL", "message": "User Information successfully updated"}, status=status.HTTP_200_OK)
        else:
            raise ValidationError({"response": "FAILED", "message": "There is no matching user"}, status=status.HTTP_400_BAD_REQUEST)
         