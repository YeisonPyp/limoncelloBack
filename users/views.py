from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied
from users.models import People, Users
from users.serializers import PeopleSerializer, UsersSerializer, LoginSerializer, UsersListSerializer, UserDetailSerializer, PeopleUpdateSerializer, UserUpdateSerializer
from security.models import Roles, UserRoles
from security.views import UserRolesCreate
from security.permissions import HasPermission
from bookings import utils, models
from django.contrib.auth.hashers import make_password, check_password
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
import random
import string
from datetime import datetime

class PeopleCreate(generics.ListCreateAPIView):
    serializer_class = PeopleSerializer

    def create_person(self, person_data):
        serializer = self.serializer_class(data=person_data)
        if serializer.is_valid():
            serializer.save()
            return serializer.data
        raise ValidationError({'success': False, 'message': 'Invalid data', 'errors': serializer.errors})

    def post(self, request, *args, **kwargs):
        data = request.data
        if not data:
            raise ValidationError({'success': False, 'message': 'No data provided'})
        
        person = self.create_person(data)
        return Response({'success': True, 'message': 'Person created successfully', 'data': person}, status=status.HTTP_201_CREATED)
    

class UserCreate(generics.ListCreateAPIView):
    serializer_class = UsersSerializer
    #permission_classes = [permissions.IsAuthenticated, HasPermission]

    def create_person(self, person_data):
        instance_people = PeopleCreate()
        person = instance_people.create_person(person_data)
        try:
            person = People.objects.get(person_id=person['person_id'])
        except People.DoesNotExist:
            raise NotFound('Person not found')
        
        return person
    
    def create_username(self, first_name, first_last_name):
        username = first_name.lower() + '.' + first_last_name.lower()
        username = username.replace(' ', '')
        if Users.objects.filter(username=username).exists():
            username = username + str(Users.objects.count() + 1)
        return username

    def create_user(self, user_data):
        serializer = self.serializer_class(data=user_data)
        if serializer.is_valid():
            serializer.save()
            return serializer.data
        raise ValidationError({'success': False, 'message': 'Invalid data', 'errors': serializer.errors})

    def create_role_user(self, role_id, user_id):
        try:
            role = Roles.objects.get(role_id=role_id)
        except Roles.DoesNotExist:
            raise NotFound({'success': False, 'message': 'Role not found'})
        
        try:
            user = Users.objects.get(user_id=user_id)
        except Users.DoesNotExist:
            raise NotFound({'success': False, 'message': 'User not found'})
        
        instance_user_roles = UserRolesCreate()
        
        user_role = instance_user_roles.create_role_user(role.role_id, user.user_id)
        return user_role
        

    def post(self, request, *args, **kwargs):
        data = request.data
        if not data:
            raise ValidationError({'success': False, 'message': 'No data provided'})

        try:
            role = Roles.objects.get(role_id=data['role_id'])
        except Roles.DoesNotExist:
            raise NotFound({'success': False, 'message': 'Role not found'})
        
        person = People.objects.filter(identification=data['identification']).exists()
        if not person:
            person_data = {
                'identification': data['identification'],
                'first_name': str(data['first_name']).upper(),
                'second_name': str(data['second_name']).upper() if data['second_name'] else None,
                'first_last_name': str(data['first_last_name']).upper(),
                'second_last_name': str(data['second_last_name']).upper() if data['second_last_name'] else None,
                'date_of_birth': data['date_of_birth'],
                'phone_number': data['phone_number'],
                'email': str(data['email']).upper(),
                'send_email': True
            }
            person = self.create_person(person_data)

            data_user = {
            'username': self.create_username(person.first_name, person.first_last_name),
            'password_hash': make_password(data['identification']),
            'is_locked': False,
            'is_active': True,
            'person_id': person.person_id
            }
            
            user = self.create_user(data_user)
            user_role = self.create_role_user(role.role_id, user['user_id'])

            name = person.first_name + ' ' + person.first_last_name

            try:
                utils.enviar_correo_confirmacion_creacion_usuario(person.email, name, user['username'], data['identification'])
            except Exception as e:
                return Response({'success': False, 'message': f'Error sending email: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            
            return Response({'success': True, 'message': 'User created successfully', 'data': user}, status=status.HTTP_201_CREATED)
        else:
            raise ValidationError({'success': False, 'message': 'Person already exists'})
            

class UserList(generics.ListAPIView):
    serializer_class = UsersListSerializer
    # permission_classes = [permissions.IsAuthenticated, HasPermission]

    def get(self, request, *args, **kwargs):
        users = Users.objects.all()
        if not users:
            raise NotFound({'success': False, 'message': 'No users found'})
        serializer = self.serializer_class(users, many=True)
        return Response({'success': True, 'message': 'Users found', 'data': serializer.data}, status=status.HTTP_200_OK)
    

class UserDetail(generics.RetrieveAPIView):
    serializer_class = UserDetailSerializer
    queryset = Users.objects.all()

    def get(self, request, user_id):
        try:
            user = self.queryset.get(user_id=user_id)
        except People.DoesNotExist:
            raise NotFound({'success': False, 'message': 'User not found'})

        if not user_id:
            raise ValidationError({'success': False, 'message': 'No user ID provided'})
        
        serializer = self.serializer_class(user)
        return Response({'success': True, 'message': 'User found', 'data': serializer.data}, status=status.HTTP_200_OK)
    

class UserUpdate(generics.UpdateAPIView):
    serializer_class = UserUpdateSerializer
    serializer_class_person = PeopleUpdateSerializer

    def update_person(self, person_id, person_data):
        try: 
            person = People.objects.get(person_id=person_id)
        except People.DoesNotExist:
            raise NotFound({'success': False, 'message': 'Person not found'})
        
        serializer = self.serializer_class_person(person, data=person_data)
        if serializer.is_valid():
            serializer.save()
            return serializer.data
        raise ValidationError({'success': False, 'message': 'Invalid data', 'errors': serializer.errors})

    def update_user(self, user_id, user_data):
        try:
            user = Users.objects.get(user_id=user_id)
        except Users.DoesNotExist:
            raise NotFound({'success': False, 'message': 'User not found'})
        
        serializer = self.serializer_class(user, data=user_data)
        if serializer.is_valid():
            serializer.save()
            return serializer.data
        raise ValidationError({'success': False, 'message': 'Invalid data', 'errors': serializer.errors})

    def put(self, request, *args, **kwargs):
        data = request.data
        user_id = data['user_id']
        person_id = data['person_id']
        today = datetime.now()

        user_data = {
            'is_active': data['is_active'],
            'is_locked': data['is_locked'],
            'modification_date': today
        }

        person_data = {
            'identification': data['identification'],
            'first_name': data['first_name'],
            'second_name': data['second_name'],
            'first_last_name': data['first_last_name'],
            'second_last_name': data['second_last_name'],
            'email': data['email'],
            'phone_number': data['phone_number'],
            'birth_date': data['birth_date'],
            'modification_date': today
        }

        if not data:
            raise ValidationError({'success': False, 'message': 'No data provided'})
        
        user = self.update_user(user_id, user_data)
        person = self.update_person(person_id, person_data)

        if not user or not person:
            raise ValidationError({'success': False, 'message': 'Error updating user or person'})

        return Response({'success': True, 'message': 'User updated successfully'}, status=status.HTTP_200_OK)


class UserDelete(generics.DestroyAPIView):
    serializer_class = UsersSerializer

    def delete_person(self, person_id):
        try:
            person = People.objects.get(person_id=person_id)
        except People.DoesNotExist:
            raise NotFound({'success': False, 'message': 'Person not found'})
        
        if not person:
            raise ValidationError({'success': False, 'message': 'Error deleting person'})
        
        if not models.Booking.objects.filter(person_id=person_id).exists():
           person.delete()
           
        return person

    def delete(self, request, user_id):
        try:
            user = Users.objects.get(user_id=user_id)
        except Users.DoesNotExist:
            raise NotFound({'success': False, 'message': 'User not found'})
        
        user.delete()
        person = self.delete_person(user.person_id.person_id)

        return Response({'success': True, 'message': 'User deleted successfully'}, status=status.HTTP_200_OK)


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = Users.objects.filter(username=serializer.validated_data['username']).first()
        if user and check_password(serializer.validated_data['password'], user.password_hash):
            if not user.is_active:
                return Response({"detail": "User account is not active."}, status=status.HTTP_403_FORBIDDEN)
            if user.is_locked:
                return Response({"detail": "User account is locked."}, status=status.HTTP_403_FORBIDDEN)
            refresh = RefreshToken.for_user(user)

            user_role = UserRoles.objects.get(user_id=user.user_id)
            role = Roles.objects.get(role_id=user_role.role_id.role_id)

            data_login = {
                'user_id': user.user_id,
                'username': user.username,
                'role_id': role.role_id,
                'campus_id': role.campus_id.campus_id,
                'campus_name': role.campus_id.name,
                'is_active': user.is_active,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }

            return Response({'success': True, 'message': 'User logged in successfully', 'data': data_login}, status=status.HTTP_200_OK)
        return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
    

class LogoutView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"success": True, "message": "User logged out successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"success": False, "message": "Invalid token", "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

class PasswordChangeForget(generics.UpdateAPIView):
    serializer_class = UsersSerializer
    queryset = Users.objects.all()

    def generate_password(self):
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        return password
    
    def update_password(self, user_id, password):
        user = self.queryset.get(user_id=user_id)
        user.password_hash = make_password(password)
        user.modification_date = datetime.now()
        user.save()
        return user

    def put(self, request, user_id):

        try:
            user = Users.objects.get(user_id=user_id)
        except Users.DoesNotExist:
            raise NotFound({'success': False, 'message': 'User not found'})
        
        name = user.person_id.first_name + ' ' + user.person_id.first_last_name
        password = self.generate_password()
        user = self.update_password(user_id, password)
        
        try:
            utils.enviar_correo_recuperacion_contraseña(user.person_id.email, name, password)
        except Exception as e:
            return Response({'success': False, 'message': f'Error sending email: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(
            {'success': True, 'message': 'Password updated successfully', 'user_id': user_id},
            status=status.HTTP_200_OK
        )


class PasswordChangeUser(generics.UpdateAPIView):
    serializer_class = UsersSerializer
    queryset = Users.objects.all()
    
    def update_password(self, user_id, password):
        user = self.queryset.get(user_id=user_id)
        user.password_hash = make_password(password)
        user.modification_date = datetime.now()
        user.save()
        return user

    def put(self, request):

        data = request.data

        if not data:
            raise ValidationError({'success': False, 'message': 'No data provided'})
        
        user_id = data['user_id']
        password = data['password']
        new_password = data['new_password']

        try:
            user = Users.objects.get(user_id=user_id)
        except Users.DoesNotExist:
            raise NotFound({'success': False, 'message': 'User not found'})
        
        if not check_password(password, user.password_hash):
            raise PermissionDenied({'success': False, 'message': 'Invalid password'})

        user = self.update_password(user_id, new_password)
        
        return Response(
            {'success': True, 'message': 'Password updated successfully', 'user_id': user_id},
            status=status.HTTP_200_OK
        )




