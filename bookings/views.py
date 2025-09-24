from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied
from bookings.models import Campus, Booking
from users.models import People
from users.views import PeopleCreate
from bookings.serializers import CampusSerializerList, CampusSerializerDetail, BookingSerializer, BookingListSerializer, BookingByIdSerializer
import bookings.utils as utils
from datetime import datetime


class CampusList(generics.ListAPIView):
    serializer_class = CampusSerializerList

    def get(self, request, *args, **kwargs):
        campus = Campus.objects.all()
        serializer = self.serializer_class(campus, many=True)
        return Response({'success': True, 'message': 'Campus List', 'data': serializer.data}, status=status.HTTP_200_OK)
    

class CampusDetail(generics.RetrieveAPIView):
    queryset = Campus.objects.all()
    serializer_class = CampusSerializerDetail

    def get(self, request, campus_id):
        if not campus_id:
            raise ValidationError('Missing required fields')
        
        try:
            campus = Campus.objects.get(campus_id=campus_id)
        except Campus.DoesNotExist:
            raise NotFound('Campus not found')
        
        campus = Campus.objects.get(campus_id=campus_id)
        serializer = self.serializer_class(campus)
        return Response({'success': True, 'message': 'Campus Detail', 'data': serializer.data}, status=status.HTTP_200_OK)


class BookingHourList(generics.ListAPIView):

    def get(self, request):
        data = request.query_params
        campus_id = data.get('campus_id')
        booking_date = data.get('booking_date')
        people_amount = data.get('people_amount')

        if not campus_id or not booking_date: 
            raise ValidationError('Missing required fields')
        
        if not Campus.objects.filter(campus_id=campus_id).exists():
            raise NotFound('Campus not found')
        
        campus = Campus.objects.get(campus_id=campus_id)
        hours_list = utils.obtener_horarios_permitidos(campus.campus_id, booking_date, people_amount)
        hours_list = [utils.convert_to_am_pm(hour) for hour in hours_list]

        
        return Response({'success': True, 'message': 'Hours List', 'data': hours_list}, status=status.HTTP_200_OK)


class BookingCreate(generics.ListCreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

    def create_person(self, person_data):
        instance_people = PeopleCreate()
        person = instance_people.create_person(person_data)
        try:
            person = People.objects.get(person_id=person['person_id'])
        except People.DoesNotExist:
            raise NotFound('Person not found')
        
        return person
    
    def create_booking(self, booking_data):

        serializer = self.serializer_class(data=booking_data)
        if serializer.is_valid():
            serializer.save()
            return serializer.data
        raise ValidationError('Invalid data', serializer.errors)
    
    def validate_booking(self, booking_data):
        booking = Booking.objects.filter(campus_id=booking_data['campus_id'], person_id=booking_data['person_id'], active=True)
        if booking.exists():
            for book in booking:
                date = datetime.strptime(booking_data['booking_date'], "%Y-%m-%d").date()
                if book.booking_date == date:
                    raise ValidationError('Booking already exists')
        
    def post(self, request, *args, **kwargs):
        data = request.data

        if not data:
            raise ValidationError('No data provided')
        
        person = People.objects.filter(email=str(data['email']).upper()).exists()
        if not person:
            names = str(data['name'])
            apellidos = str(data['last_name'])
            person_data = {
                'identification': "2222222222",
                'first_name': names.split(' ')[0].upper(),
                'second_name': names.split(' ')[1].upper() if len(names.split(' ')) > 1 else None,
                'first_last_name': apellidos.split(' ')[0].upper(),
                'second_last_name': apellidos.split(' ')[1].upper() if len(apellidos.split(' ')) > 1 else None,
                'date_of_birth': data['date_of_birth'],
                'phone_number': data['phone_number'],
                'email': str(data['email']).upper(),
                'send_email': data['send_email']
            }
            person = self.create_person(person_data)
        else:
            person = People.objects.filter(email=str(data['email']).upper()).first()
        
        campus_id = data['campus_id']
        people_amount = data['people_amount']
        booking_date = data['booking_date']
        booking_hour = data['booking_hour']
        observations = data['observations']

        if not campus_id or not people_amount or not booking_date or not booking_hour:
            raise ValidationError('Missing required fields')
        
        if not isinstance(people_amount, int) or people_amount <= 0:
            raise ValidationError('Invalid people amount')
        
        if not isinstance(booking_date, str) or not isinstance(booking_hour, str):
            raise ValidationError('Invalid date or hour')
        
        try:
            campus = Campus.objects.get(campus_id=campus_id)
        except Campus.DoesNotExist:
            raise NotFound('Campus not found')

        booking_data = {
            'person_id': person.person_id,
            'campus_id': campus.campus_id,
            'people_amount': people_amount,
            'booking_date': booking_date,
            'booking_hour': utils.convert_to_24(booking_hour),
            'observations': observations,
            'active': True,
            'approved': False
        }

        self.validate_booking(booking_data)

        booking = self.create_booking(booking_data)
        observaciones = booking_data['observations'] if booking_data['observations'] != "" else 'Sin observaciones'
        try:
            utils.enviar_correo_confirmacion_reserva(person.email, f'{person.first_name} {person.first_last_name}', booking_data['booking_date'], booking_data['booking_hour'], campus.name, booking_data['people_amount'], observaciones, 'confirmada')
            utils.enviar_correo_confirmacion_reserva_sede(campus.email, campus.name, f'{person.first_name} {person.first_last_name}', booking_data['booking_date'], booking_data['booking_hour'], booking_data['people_amount'], person.phone_number, observaciones, 'confirmada')
        except Exception as e:
            return Response({'success': False, 'message': f'Error sending email: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
        return Response({'success': True, 'message': 'Booking created successfully', 'data': booking}, status=status.HTTP_201_CREATED)


class BookingList(generics.ListAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingListSerializer

    def get(self, request, campus_id):  

        booking_date = datetime.now().strftime('%Y-%m-%d')
        try:
            campus = Campus.objects.get(campus_id=campus_id)
        except Campus.DoesNotExist:
            raise NotFound('Campus not found')
        
        campus = Campus.objects.get(campus_id=campus_id)

        # bookings = Booking.objects.filter(campus_id=campus.campus_id, booking_date=booking_date).order_by('booking_hour')

        bookings = Booking.objects.filter(campus_id=campus.campus_id, booking_date__gte=booking_date).order_by('booking_date', 'booking_hour')

        serializer = self.serializer_class(bookings, many=True)
        return Response({'success': True, 'message': 'Booking List', 'data': serializer.data}, status=status.HTTP_200_OK)
        

class BookingByIdView(generics.RetrieveAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingByIdSerializer

    def get(self, request, booking_id):

        if not booking_id:
            raise ValidationError('Missing required fields')
        
        if not Booking.objects.filter(booking_id=booking_id).exists():
            raise NotFound('Booking not found')
        
        booking = Booking.objects.get(booking_id=booking_id)
        serializer = self.serializer_class(booking)
        return Response({'success': True, 'message': 'Booking Detail', 'data': serializer.data}, status=status.HTTP_200_OK)


class BookingActivasByPersonView(generics.ListAPIView):
    serializer_class = BookingListSerializer

    def get(self, request, person_id):

        if not person_id:
            raise ValidationError('Missing required fields')

        bookings = Booking.objects.filter(person_id=person_id, active=True)
        serializer = self.serializer_class(bookings, many=True)
        return Response({'success': True, 'message': 'Active Bookings List', 'data': serializer.data}, status=status.HTTP_200_OK)
    

class BookingUpdate(generics.UpdateAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

    def update(self, request):
        data = request.data
        booking_id = data.get('booking_id')
        booking_status = data.get('status')

        if not booking_id or not booking_status:
            raise ValidationError('Missing required fields')
        
        try:
            booking = Booking.objects.get(booking_id=booking_id)
        except Booking.DoesNotExist:
            raise NotFound('Booking not found')
        
        if booking_status == 'approved':
            booking.approved = True
            booking.active = False
            booking.save()
            return Response({'success': True, 'message': 'Booking approved successfully'}, status=status.HTTP_200_OK)
        
        if booking_status == 'cancelled':
            person = People.objects.get(person_id=booking.person_id.person_id)
            campus = Campus.objects.get(campus_id=booking.campus_id.campus_id)
            observaciones = booking.observations if booking.observations != "" else 'Sin observaciones'
            booking.active = False
            booking.save()

            try:
                utils.enviar_correo_confirmacion_reserva(person.email, f'{person.first_name} {person.first_last_name}', booking.booking_date, booking.booking_hour, campus.name, booking.people_amount, observaciones, 'cancelada')
                utils.enviar_correo_confirmacion_reserva_sede(campus.email, campus.name, f'{person.first_name} {person.first_last_name}', booking.booking_date, booking.booking_hour, booking.people_amount, person.phone_number, observaciones, 'cancelada')
        
            except Exception as e:
                return Response({'success': False, 'message': f'Error sending email: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({'success': True, 'message': 'Booking cancelled successfully'}, status=status.HTTP_200_OK)

        raise ValidationError('Invalid status')