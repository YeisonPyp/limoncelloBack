from rest_framework import serializers
from bookings.models import Campus, Booking
from users.models import People

class CampusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campus
        fields = '__all__'


class CampusSerializerDetail(serializers.ModelSerializer):
    class Meta:
        model = Campus
        fields = ['campus_id', 'name', 'address']


class CampusSerializerList(serializers.ModelSerializer):
    class Meta:
        model = Campus
        fields = ['campus_id', 'name']


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'


class BookingListSerializer(serializers.ModelSerializer):
    name_person = serializers.SerializerMethodField()
    state = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = ['booking_id', 'campus_id', 'person_id', 'name_person', 'booking_date', 'booking_hour', 'people_amount', 'state']
    
    def get_name_person(self, obj):
        person = People.objects.get(person_id=obj.person_id.person_id)
        return person.first_name + ' ' + person.first_last_name
    
    def get_state(self, obj):
        if obj.approved and not obj.active:
            state = 'GESTIONADA'
        elif obj.active and not obj.approved:
            state = 'PENDIENTE'
        else:
            state = 'CANCELADA'
        return state


class BookingByIdSerializer(serializers.ModelSerializer):
    name_person = serializers.SerializerMethodField()
    phone_person = serializers.ReadOnlyField(source='person_id.phone_number')
    email_person = serializers.ReadOnlyField(source='person_id.email')
    state = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = ['booking_id', 'campus_id', 'person_id', 'name_person', 'phone_person', 'email_person', 'booking_date', 'booking_hour', 'people_amount', 'observations', 'state']
    
    def get_name_person(self, obj):
        person = People.objects.get(person_id=obj.person_id.person_id)
        full_name = ' '.join(filter(None, [person.first_name, person.second_name, person.first_last_name, person.second_last_name]))
        return full_name
    
    def get_state(self, obj):
        if obj.active and obj.approved:
            state = 'GESTIONADA'
        elif obj.active and not obj.approved:
            state = 'PENDIENTE'
        else:
            state = 'CANCELADA'
        return state

