from django.urls import path
from . import views

app_name = 'meditation'

urlpatterns = [
    path('', views.front, name='front'),
    path('home/', views.home, name='home'),
    # path('categories/', views.category_list, name='category_list'),
    # path('categories/<int:category_id>/', views.category_detail, name='category_detail'),
    # path('subcategories/<int:subcategory_id>/', views.subcategory_detail, name='subcategory_detail'),
    # path('techniques/<int:technique_id>/', views.technique_detail, name='technique_detail'),
    path('library/', views.library, name='library'),
    path('community/', views.community, name='community'),
    path('settings/', views.settings_page, name='settings'),



    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('techniques/<int:pk>/', views.TechniqueDetailView.as_view(), name='technique_detail'),
    path('techniques/<int:pk>/favorite/', views.toggle_favorite, name='toggle_favorite'),

     # Community URLs
    path('community/', views.community_home, name='community_home'),
    path('session/<int:session_id>/', views.session_detail, name='session_detail'),
    path('session/<int:session_id>/register/', views.register_for_session, name='register_for_session'),
    path('session/<int:session_id>/join/', views.join_live_session, name='join_live_session'),
    path('my-sessions/', views.my_sessions, name='my_sessions'),
    path('my-sessions-quick/', views.my_sessions_quick, name='my_sessions_quick'),
    
    # Expert URLs
    path('expert/dashboard/', views.expert_dashboard, name='expert_dashboard'),
    path('session/<int:session_id>/attendees/', views.session_attendees, name='session_attendees'),
    
]