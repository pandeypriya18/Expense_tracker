from django.urls import reverse

from account.models import MyUser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from account.serializers import RegisterSerializer,LoginSerializer,ChangePasswordSerializer , ForgetPasswordSerializer , UserSerializer,ResetPasswordSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework import permissions
from django.conf import settings   
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode , urlsafe_base64_decode
from django.utils.encoding import force_bytes , force_str
from django.contrib.auth.tokens import PasswordResetTokenGenerator

class RegisterView(APIView):

  def post(self, request):
     serializer = RegisterSerializer(data = request.data)
     if serializer.is_valid(raise_exception=True):
        serializer.create_user(serializer.validated_data)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
     return Response(serializer.error_messages, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
   serializer_class = LoginSerializer
   def post(self ,request):
      serializer = self.serializer_class(data=request.data)
      if serializer.is_valid():
         user = serializer.validated_data["user"]

         refresh = RefreshToken.for_user(user)

         return Response({"message":"Login successful.", "refresh": str(refresh), "access": str(refresh.access_token)}, status=status.HTTP_200_OK)
      return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MeView(APIView):
   def get(self , request):
      serializer = UserSerializer(request.user)
      return Response(serializer.data)
      
class LogoutView(APIView):

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]

            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {"message": "Logout successful"},
                status=status.HTTP_200_OK
            )

        except TokenError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class ChangePasswordView(APIView):
   permission_classes = [permissions.IsAuthenticated]
   serializer_class = ChangePasswordSerializer

   def post(self, request):
      serializer = ChangePasswordSerializer(data = request.data , 
                                            context = {"request":request})
      if serializer.is_valid():
         user = request.user
         user.set_password(serializer.validated_data["new_password"])
         user.save()

         return Response({"message":"Password Changed Successfully."},status=status.HTTP_200_OK)
      return Response(serializer.errors , status=status.HTTP_400_BAD_REQUEST)

class ForgetPasswordView(APIView):

   def post(self, request):
      serializer = ForgetPasswordSerializer(data = request.data)

      if not serializer.is_valid():
         return Response(serializer.errors , status=status.HTTP_404_NOT_FOUND)

      email = serializer.validated_data["email"]

      
      user = MyUser.objects.get(email=email)
      if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = PasswordResetTokenGenerator().make_token(user)
            path = reverse('reset-password',kwargs={"uid":uid , "token":token})
            link = request.build_absolute_uri(path)
            print(link)
            send_mail(
               subject="Reset your password",
               message=f"Click the link to reset your password:\n{link}",
               from_email=settings.DEFAULT_FROM_EMAIL,
               recipient_list=[user.email],
               )
      return Response({"message":"If email exists , Reset link has been sent."} , status = status.HTTP_200_OK)

class ResetPasswordView(APIView):
   def get_user(self, uid,token):
      try:
         id = urlsafe_base64_decode(uid)
         user = MyUser.objects.get(pk=id)
      except MyUser.DoesNotExist:
         return None
      if not PasswordResetTokenGenerator().check_token( user , token):
         return None
      return user
   def get(self, request, uid,token):
        if not self.get_user(uid, token):
            return Response({"error": "Invalid or expired link."},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Valid link"})

   def post(self, request, uid, token):
        user = self.get_user(uid, token)
        if not user:
            return Response({"error": "Invalid or expired link."},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user.set_password(serializer.validated_data["new_password"])
        user.save()
        return Response({"message": "Password Changed Successfully."})
