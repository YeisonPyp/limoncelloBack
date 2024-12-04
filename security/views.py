from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied
from users.models import People, Users
from bookings.models import Campus
from users.serializers import PeopleSerializer, UsersSerializer
from security.models import Roles
from security.serializers import RolesSerializer, UserRolesSerializer


class RolesCreate(generics.ListCreateAPIView):
    serializer_class = RolesSerializer

    def create_role(self, role_data):
        serializer = self.serializer_class(data=role_data)
        if serializer.is_valid():
            serializer.save()
            return serializer.data
        raise ValidationError({'success': False, 'message': 'Invalid data', 'errors': serializer.errors})

    def post(self, request, *args, **kwargs):
        data = request.data
        if not data:
            raise ValidationError({'success': False, 'message': 'No data provided'})
        
        role = self.create_role(data)
        return Response({'success': True, 'message': 'Role created successfully', 'data': role}, status=status.HTTP_201_CREATED)
    

class RolesList(generics.ListAPIView):
    serializer_class = RolesSerializer

    def get(self, request):

        roles = Roles.objects.all()
        if not roles:
            raise NotFound({'success': False, 'message': 'No roles found'})
        
        serializer = self.serializer_class(roles, many=True)
        return Response({'success': True, 'message': 'Roles retrieved successfully', 'data': serializer.data}, status=status.HTTP_200_OK)
    

class RolesListByCampus(generics.ListAPIView):
    serializer_class = RolesSerializer

    def get(self, request, campus_id):

        try:
            campus = Campus.objects.get(campus_id=campus_id)
        except Campus.DoesNotExist:
            raise NotFound({'success': False, 'message': 'Campus not found'})
        
        roles = Roles.objects.filter(campus_id=campus_id)
        if not roles:
            raise NotFound({'success': False, 'message': 'No roles found'})
        
        serializer = self.serializer_class(roles, many=True)
        return Response({'success': True, 'message': 'Roles retrieved successfully', 'data': serializer.data}, status=status.HTTP_200_OK)
    

class UserRolesCreate(generics.CreateAPIView):
    serializer_class = UserRolesSerializer

    def create_role_user(self, role_id, user_id):
        try:
            role = Roles.objects.get(role_id=role_id)
        except Roles.DoesNotExist:
            raise NotFound({'success': False, 'message': 'Role not found'})
        
        try:
            user = Users.objects.get(user_id=user_id)
        except Users.DoesNotExist:
            raise NotFound({'success': False, 'message': 'User not found'})
        
        user_role = {
            'role_id': role_id,
            'user_id': user_id
        }
        serializer = self.serializer_class(data=user_role)
        if serializer.is_valid():
            serializer.save()
            return serializer.data
        raise ValidationError({'success': False, 'message': 'Invalid data', 'errors': serializer.errors})
    
    def post(self, request, *args, **kwargs):
        data = request.data
        if not data:
            raise ValidationError({'success': False, 'message': 'No data provided'})
        
        role_id = data['role_id']
        user_id = data['user_id']
        if not role_id or not user_id:
            raise ValidationError({'success': False, 'message': 'Role ID and User ID are required'})
        
        response = self.create_role_user(role_id, user_id)
        return Response({'success': True, 'message': 'Role assigned to user successfully', 'data': response}, status=status.HTTP_201_CREATED)
