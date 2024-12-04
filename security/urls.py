from django.urls import path
import security.views as views

urlpatterns = [
    path('roles/', views.RolesCreate.as_view(), name='roles_create'),
    path('roles/list/', views.RolesList.as_view(), name='roles_list'),
    path('roles/list/<int:campus_id>/', views.RolesListByCampus.as_view(), name='roles_list_by_campus'),

]