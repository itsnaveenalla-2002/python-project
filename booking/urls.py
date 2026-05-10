from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),

    path('register/', views.register, name='register'),
    
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('dashboard/', views.dashboard, name='dashboard'),

    # ✅ FIXED (renamed from admin → dashboard)
    path('dashboard/users/', views.view_users, name='view_users'),
    path('dashboard/tutors/', views.view_tutors, name='view_tutors'),
    path('dashboard/approve/<int:user_id>/', views.approve_tutor, name='approve_tutor'),
    # Admin advanced features
    path('dashboard/delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('dashboard/all-slots-admin/', views.all_slots_admin, name='all_slots_admin'),
    path('dashboard/all-bookings/', views.all_bookings, name='all_bookings'),
    path('dashboard/cancel-booking/<int:booking_id>/', views.admin_cancel_booking, name='admin_cancel_booking'),

    path('dashboard/create-slot/', views.create_slot, name='create_slot'),
    path('dashboard/my-slots/', views.my_slots, name='my_slots'),

    path('dashboard/all-slots/', views.all_slots, name='all_slots'),
    path('dashboard/book/<int:slot_id>/', views.book_slot, name='book_slot'),
    path('dashboard/my-bookings/', views.my_bookings, name='my_bookings'),
    path('dashboard/cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('dashboard/reassign/<int:booking_id>/', views.reassign_booking, name='reassign_booking'),
    
]