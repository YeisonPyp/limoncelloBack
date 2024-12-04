from django.urls import path
import users.views as views

urlpatterns = [
    path('person-create/', views.PeopleCreate.as_view(), name='people_create'),
    path('user-create/', views.UserCreate.as_view(), name='user_create'),
    path('user-list/', views.UserList.as_view(), name='user_list'),
    path('user-detail/<int:user_id>/', views.UserDetail.as_view(), name='user_detail'),
    path('user-update/', views.UserUpdate.as_view(), name='user_update'),
    path('user-delete/<int:user_id>/', views.UserDelete.as_view(), name='user_delete'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('password-change/<int:user_id>/', views.PasswordChangeForget.as_view(), name='password_change'),
    path('password-change-user/', views.PasswordChangeUser.as_view(), name='password_change_user'),



]