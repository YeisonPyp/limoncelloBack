from django.urls import path
import bookings.views as views

urlpatterns = [
    path('list-campuses/', views.CampusList.as_view(), name='list_campuses'),
    path('campus-details/<int:campus_id>/', views.CampusDetail.as_view(), name='campus_by_id'),
    path('list-hours/', views.BookingHourList.as_view(), name='list_hours'),
    path('create-booking/', views.BookingCreate.as_view(), name='create_booking'),
    path('list-bookings/<int:campus_id>/', views.BookingList.as_view(), name='list_bookings'),
    path('booking-id/<int:booking_id>/', views.BookingByIdView.as_view(), name='booking_by_id'),
    path('booking-by-person/<int:person_id>/', views.BookingActivasByPersonView.as_view(), name='booking_by_person'),
    path('update-booking/', views.BookingUpdate.as_view(), name='update_booking'),

]