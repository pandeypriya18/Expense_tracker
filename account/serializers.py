from rest_framework import serializers
from account.models import MyUser
from rest_framework.exceptions import ValidationError


class RegisterSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)

    def validate(self, data):
            if data['password'] != data['password2']:
                raise serializers.ValidationError({"error":"Passwords do not match."})
    
            return data
            
    def validate_email(self,value):
            if MyUser.objects.filter(email=value).exists():
                raise serializers.ValidationError("Email already exists.")
    
            return value
            
    def create_user(self, validated_data):
            validated_data.pop("password2")
    
            user = MyUser.objects.create_user(
                **validated_data
            )
            return user 

    def validate_role(self, value):
        if value not in ["admin", "user"]:
            raise serializers.ValidationError(
                "Invalid role. Choose admin or user."
            )
        return value

    class Meta:
        model = MyUser
        fields = ['email','username','password','password2','role']
        extra_kwargs = {
            "password": {"write_only": True}
        }

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        try:
            user = MyUser.objects.get(email=data["email"])
        except MyUser.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password.")

        if not user.check_password(data["password"]):
            raise serializers.ValidationError("Invalid email or password.")

        if not user.is_active:
            raise serializers.ValidationError("Account is inactive.")

        data["user"] = user
        return data
    
class ChangePasswordSerializer(serializers.Serializer):
     old_password = serializers.CharField(write_only = True , required = True)
     new_password = serializers.CharField(write_only=True , required= True)
     confirm_password = serializers.CharField(write_only=True , required=True)

     def validate(self , data):
          user = self.context["request"].user

          if not user.check_password(data["old_password"]):
               raise ValidationError({"old_password":"Old password is Incorrect."})

          if data["new_password"] == data["old_password"]:
               raise ValidationError({"error":"Please Enter a different password."})

          if data["new_password"] != data["confirm_password"]:
               raise ValidationError({"error":"New password and Confirm password must be same."})
          return data

class ForgetPasswordSerializer(serializers.Serializer):
     email = serializers.EmailField( max_length=200)

     def validate_email(self ,value):
          if not MyUser.objects.filter(email=value).exists():
               raise ValidationError({"error":"This email doesn't exists."})
          return value

class UserSerializer(serializers.ModelSerializer):
     class Meta:
          model = MyUser
          fields = ['id','username','role','email']

class ResetPasswordSerializer(serializers.Serializer):
      new_password = serializers.CharField(write_only=True , required= True)
      confirm_password = serializers.CharField(write_only=True , required=True)

      def validate(self, data):
           if data["new_password"] != data["confirm_password"]:
                raise ValidationError({"error":"New password and confirm password should be same."})
           return data