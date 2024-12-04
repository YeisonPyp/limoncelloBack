from rest_framework import serializers
from users.models import People, Users
from security.models import UserRoles

class PeopleSerializer(serializers.ModelSerializer):
    class Meta:
        model = People
        fields = '__all__'


class PeopleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = People
        fields = ['identification', 'first_name', 'second_name', 'first_last_name', 'second_last_name', 'email', 'phone_number', 'birth_date']


class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = '__all__'
    

class UsersListSerializer(serializers.ModelSerializer):
    role_user = serializers.SerializerMethodField()
    name_person = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = ['user_id', 'username', 'name_person', 'role_user', 'is_active', 'is_locked']

    def get_name_person(self, obj):
        person = People.objects.get(person_id=obj.person_id.person_id)
        full_name = ' '.join(filter(None, [person.first_name, person.second_name, person.first_last_name, person.second_last_name]))
        return full_name

    def get_role_user(self, obj):
        try:
            role_user = UserRoles.objects.get(user_id=obj.user_id)
            return role_user.role_id.role_name
        except UserRoles.DoesNotExist:
            return None
        

class UserDetailSerializer(serializers.ModelSerializer):
    role_user = serializers.SerializerMethodField()
    identification = serializers.ReadOnlyField(source='person_id.identification')
    first_name = serializers.ReadOnlyField(source='person_id.first_name')
    second_name = serializers.ReadOnlyField(source='person_id.second_name')
    first_last_name = serializers.ReadOnlyField(source='person_id.first_last_name')
    second_last_name = serializers.ReadOnlyField(source='person_id.second_last_name')
    email = serializers.ReadOnlyField(source='person_id.email')
    phone_number = serializers.ReadOnlyField(source='person_id.phone_number')
    birth_date = serializers.ReadOnlyField(source='person_id.date_of_birth')

    class Meta:
        model = Users
        fields = ['user_id', 'username', 'identification', 'first_name', 'second_name', 'first_last_name', 'second_last_name', 'email', 'phone_number', 'birth_date', 'is_active', 'is_locked']

    def get_role_user(self, obj):
        try:
            role_user = UserRoles.objects.get(user_id=obj.user_id)
            return role_user.role_id.role_name
        except UserRoles.DoesNotExist:
            return None
        

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ['is_active', 'is_locked']


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


