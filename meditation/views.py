from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic
from .models import Category, Subcategory, MeditationTechnique, User, Comment
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from django.contrib import messages
from .models import LiveSession, ExpertProfile, SessionRegistration
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, View
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.db.models import Q
from .models import Category, Technique, Favorite
from django.core.paginator import Paginator


class HomeView(View):
    def get(self, request):
        time_of_day = Technique.get_time_of_day()
        techniques = Technique.objects.filter(
            Q(time_of_day=time_of_day) | Q(time_of_day=None)
        ).order_by('?')[:6]  # Get random techniques for current time of day
        
        return render(request, 'home.html', {
            'techniques': techniques,
            'time_of_day': time_of_day,
        })


class CategoryListView(ListView):
    model = Category
    template_name = 'categories/list.html'
    context_object_name = 'categories'


class CategoryDetailView(DetailView):
    model = Category
    template_name = 'categories/detail.html'
    context_object_name = 'category'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get techniques for this category with pagination
        techniques_list = self.object.techniques.all()
        paginator = Paginator(techniques_list, 10)  # 10 techniques per page
        page = self.request.GET.get('page', 1)
        techniques = paginator.get_page(page)
        
        context['techniques'] = techniques
        
        # Get filters from GET parameters
        difficulty = self.request.GET.get('difficulty')
        duration = self.request.GET.get('duration')
        
        # Apply filters if provided
        if difficulty:
            techniques_list = techniques_list.filter(difficulty=difficulty)
        
        if duration:
            # Example: if duration is 'short', filter for under 10 minutes
            if duration == 'short':
                techniques_list = techniques_list.filter(duration__lt=10)
            elif duration == 'medium':
                techniques_list = techniques_list.filter(duration__gte=10, duration__lt=30)
            elif duration == 'long':
                techniques_list = techniques_list.filter(duration__gte=30)
        
        return context


class TechniqueDetailView(DetailView):
    model = Technique
    template_name = 'categories/technique_detail.html'
    context_object_name = 'technique'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Check if technique is in user's favorites
        if self.request.user.is_authenticated:
            context['is_favorite'] = Favorite.objects.filter(
                user=self.request.user,
                technique=self.object
            ).exists()
        
        return context


@login_required
def toggle_favorite(request, pk):
    technique = get_object_or_404(Technique, pk=pk)
    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        technique=technique
    )
    
    # If favorite existed and wasn't created, then delete it
    if not created:
        favorite.delete()
        is_favorite = False
    else:
        is_favorite = True
    
    # If AJAX request, return JSON response
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'is_favorite': is_favorite
        })
    
    # Otherwise redirect back to technique detail
    return redirect('technique_detail', pk=pk)


# def community_home(request):
#     current_time = timezone.now()

#     upcoming_sessions = LiveSession.objects.filter(
#         start_time__gt=current_time,
#         status='scheduled'
#     ).order_by('start_time')[:5]

#     live_sessions = LiveSession.objects.filter(
#         start_time__lte=current_time,
#         end_time__gte=current_time,
#         status='live'
#     )

#     featured_experts = ExpertProfile.objects.filter(is_verified=True)[:6]

#     context = {
#         'upcoming_sessions': upcoming_sessions,
#         'live_sessions': live_sessions,
#         'featured_experts': featured_experts,
#     }

#     return render(request, 'community.html', context)


def community_home(request):
    now = timezone.now()
    
    # Get live sessions
    live_sessions = LiveSession.objects.filter(
        start_time__lte=now,
        end_time__gte=now,
        status='live'  # Changed from 'active' to match your model's STATUS_CHOICES
    )
    
    # Get upcoming sessions
    upcoming_sessions = LiveSession.objects.filter(
        start_time__gt=now,
        status='scheduled'  # Changed from 'active' to match your model's STATUS_CHOICES
    ).order_by('start_time')
    
    # Get featured experts
    featured_experts = ExpertProfile.objects.filter(
        is_verified=True  # Changed from is_expert and is_featured which don't exist in your model
    )
    
    context = {
        'live_sessions': live_sessions,
        'upcoming_sessions': upcoming_sessions,
        'featured_experts': featured_experts,
    }
    
    return render(request, 'meditation/community.html', context)

    from django.http import JsonResponse
from django.utils import timezone

def my_sessions_quick(request):
    """API endpoint to get a quick view of user's sessions for AJAX"""
    if not request.user.is_authenticated:
        return JsonResponse({'sessions': []})
    
    now = timezone.now()
    registrations = SessionRegistration.objects.filter(
        user=request.user
    ).select_related('session').order_by('session__start_time')
    
    sessions = []
    for reg in registrations:
        session = reg.session
        if session.start_time > now and session.status != 'cancelled':
            sessions.append({
                'id': session.id,
                'title': session.title,
                'date': session.start_time.strftime('%b %d, %Y'),
                'time': session.start_time.strftime('%I:%M %p'),
                'status': session.status
            })
            # Limit to 3 upcoming sessions for quick view
            if len(sessions) >= 3:
                break
                
    return JsonResponse({'sessions': sessions})



@login_required
def session_detail(request, session_id):
    session = get_object_or_404(LiveSession, id=session_id)
    
    # Check if user is registered
    is_registered = False
    if request.user.is_authenticated:
        is_registered = SessionRegistration.objects.filter(
            user=request.user, 
            session=session
        ).exists()
    
    # Get session host details
    host = session.host
    
    # Get other sessions by this host
    other_sessions = LiveSession.objects.filter(
        host=host
    ).exclude(id=session_id).order_by('start_time')[:3]
    
    context = {
        'session': session,
        'is_registered': is_registered,
        'host': host,
        'other_sessions': other_sessions,
    }
    
    return render(request, 'session_detail.html', context)

@login_required
def register_for_session(request, session_id):
    if request.method == 'POST':
        session = get_object_or_404(LiveSession, id=session_id)
        
        # Check if registration is full
        if session.registrations.count() >= session.max_participants:
            messages.error(request, "This session is already full.")
            return redirect('session_detail', session_id=session_id)
        
        # Check if already registered
        if SessionRegistration.objects.filter(user=request.user, session=session).exists():
            messages.info(request, "You are already registered for this session.")
        else:
            # Create new registration
            SessionRegistration.objects.create(user=request.user, session=session)
            messages.success(request, f"Successfully registered for {session.title}!")
        
        return redirect('session_detail', session_id=session_id)
    
    return redirect('community_home')

@login_required
def join_live_session(request, session_id):
    session = get_object_or_404(LiveSession, id=session_id)
    
    # Check if session is live
    if not session.is_live:
        if session.has_ended:
            messages.error(request, "This session has already ended.")
        else:
            messages.error(request, "This session hasn't started yet.")
        return redirect('session_detail', session_id=session_id)
    
    # Check if user is registered
    is_registered = SessionRegistration.objects.filter(
        user=request.user, 
        session=session
    ).exists()
    
    if not is_registered and not request.user.is_staff:
        # Auto-register user if not registered
        SessionRegistration.objects.create(user=request.user, session=session)
    
    # Mark as attended
    registration = SessionRegistration.objects.get(user=request.user, session=session)
    registration.attended = True
    registration.save()
    
    context = {
        'session': session,
        'room_name': session.room_name,
    }
    
    return render(request, 'live_session.html', context)

@login_required
def my_sessions(request):
    # Get user's registered sessions
    registrations = SessionRegistration.objects.filter(user=request.user).select_related('session')
    upcoming_sessions = [r.session for r in registrations if not r.session.has_ended]
    past_sessions = [r.session for r in registrations if r.session.has_ended]
    
    context = {
        'upcoming_sessions': upcoming_sessions,
        'past_sessions': past_sessions,
    }
    
    return render(request, 'my_sessions.html', context)

# Expert views
@login_required
def expert_dashboard(request):
    # Check if user is expert
    try:
        expert_profile = request.user.expert_profile
    except:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('community_home')
    
    # Get expert's sessions
    upcoming_sessions = LiveSession.objects.filter(
        host=expert_profile,
        end_time__gt=timezone.now()
    ).order_by('start_time')
    
    past_sessions = LiveSession.objects.filter(
        host=expert_profile,
        end_time__lt=timezone.now()
    ).order_by('-start_time')
    
    context = {
        'expert': expert_profile,
        'upcoming_sessions': upcoming_sessions,
        'past_sessions': past_sessions,
    }
    
    return render(request, 'expert_dashboard.html', context)

@login_required
def session_attendees(request, session_id):
    # Check if user is expert or admin
    try:
        expert_profile = request.user.expert_profile
    except:
        if not request.user.is_staff:
            messages.error(request, "You don't have permission to access this page.")
            return redirect('community_home')
    
    session = get_object_or_404(LiveSession, id=session_id)
    
    # Check if user is the host or an admin
    if hasattr(request.user, 'expert_profile') and session.host != request.user.expert_profile and not request.user.is_staff:
        messages.error(request, "You can only view attendees for your own sessions.")
        return redirect('expert_dashboard')
    
    # Get attendees
    registrations = SessionRegistration.objects.filter(session=session).select_related('user')
    
    context = {
        'session': session,
        'registrations': registrations,
    }
    
    return render(request, 'session_attendees.html', context)

def front(request):
    return render(request, 'front.html')


def home(request):
    categories = Category.objects.all()[:6]  # Limit to 6 categories
    
    # Get current time of day
    time_of_day = Technique.get_time_of_day()
    
    # Get techniques for current time of day
    time_based_techniques = Technique.objects.filter(
        Q(time_of_day=time_of_day) | Q(time_of_day=None)
    ).order_by('?')[:3]  # Random selection limited to 3
    
    # Get some random techniques from all categories
    random_techniques = Technique.objects.order_by('?')[:6]
    
    context = {
        'categories': categories,
        'current_time_of_day': time_of_day.capitalize(),  # 'morning' -> 'Morning'
        'time_based_techniques': time_based_techniques,
        'random_techniques': random_techniques,
    }
    
    return render(request, 'home.html', context)


def category_list(request):
    """List all categories"""
    categories = Category.objects.all()
    return render(request, 'categories/list.html', {'categories': categories})

def category_detail(request, category_id):
    """Show details of a specific category and its subcategories"""
    category = get_object_or_404(Category, id=category_id)
    subcategories = category.subcategories.all()
    
    context = {
        'category': category,
        'subcategories': subcategories,
    }
    return render(request, 'categories/detail.html', context)


def subcategory_detail(request, subcategory_id):
    """Show details of a specific subcategory and its techniques"""
    subcategory = get_object_or_404(Subcategory, id=subcategory_id)
    techniques = subcategory.techniques.all()
    
    context = {
        'subcategory': subcategory,
        'techniques': techniques,
    }
    return render(request, 'categories/subcategory_detail.html', context)

def technique_detail(request, technique_id):
    """Show detailed information about a specific meditation technique"""
    technique = get_object_or_404(MeditationTechnique, id=technique_id)
    comments = technique.comments.all().order_by('-created_at')
    
    context = {
        'technique': technique,
        'comments': comments,
    }
    return render(request, 'categories/technique_detail.html', context)





# 19-04
def library(request):
    """View for the library page"""
    techniques = MeditationTechnique.objects.all()
    
    # Filtering options
    category_filter = request.GET.get('category')
    difficulty_filter = request.GET.get('difficulty')
    duration_filter = request.GET.get('duration')
    
    if category_filter:
        techniques = techniques.filter(subcategory__category__id=category_filter)
    
    if difficulty_filter:
        techniques = techniques.filter(difficulty_level=difficulty_filter)
    
    if duration_filter:
        # Handle the duration filter
        # NOTE: Assuming duration is stored as a string in format like "10" or "30"
        # You may need to adjust this based on how your duration is actually stored
        if duration_filter == 'short':
            # Filter for short duration (5-15 minutes)
            techniques = techniques.filter(duration__gte='5', duration__lte='15')
        elif duration_filter == 'medium':
            # Filter for medium duration (15-30 minutes)
            techniques = techniques.filter(duration__gt='15', duration__lte='30')
        elif duration_filter == 'long':
            # Filter for long duration (30+ minutes)
            techniques = techniques.filter(duration__gt='30')
    
    context = {
        'techniques': techniques,
        'categories': Category.objects.all(),
    }
    return render(request, 'library.html', context)



# def library(request):
#     """View for the library page"""
#     techniques = MeditationTechnique.objects.all()
    
#     # Filtering options
#     category_filter = request.GET.get('category')
#     difficulty_filter = request.GET.get('difficulty')
#     duration_filter = request.GET.get('duration')
    
#     if category_filter:
#         techniques = techniques.filter(subcategory__category__id=category_filter)
    
#     if difficulty_filter:
#         techniques = techniques.filter(difficulty_level=difficulty_filter)
    
#     if duration_filter:
#         # Using a more complex filtering approach for text-based duration
#         # This approach will filter based on patterns in the text field
#         if duration_filter == 'short':
#             # Filter for durations likely to be short (5-15 minutes)
#             techniques = techniques.filter(
#                 Q(duration__icontains='5 min') | 
#                 Q(duration__icontains='10 min') | 
#                 Q(duration__icontains='15 min') |
#                 Q(duration__regex=r'^[0-9]+ min') # Single digit minutes
#             ).exclude(
#                 Q(duration__icontains='20 min') | 
#                 Q(duration__icontains='30 min') |
#                 Q(duration__icontains='hour')
#             )
#         elif duration_filter == 'medium':
#             # Filter for medium durations (15-30 minutes)
#             techniques = techniques.filter(
#                 Q(duration__icontains='15 min') | 
#                 Q(duration__icontains='20 min') | 
#                 Q(duration__icontains='25 min') |
#                 Q(duration__icontains='30 min')
#             ).exclude(
#                 Q(duration__icontains='hour') |
#                 Q(duration__icontains='45 min')
#             )
#         elif duration_filter == 'long':
#             # Filter for long durations (30+ minutes)
#             techniques = techniques.filter(
#                 Q(duration__icontains='30 min') | 
#                 Q(duration__icontains='45 min') | 
#                 Q(duration__icontains='hour') |
#                 Q(duration__icontains='60 min')
#             )
    
#     context = {
#         'techniques': techniques,
#         'categories': Category.objects.all(),
#     }
#     return render(request, 'library.html', context)


from users.models import CustomUser
def community(request):
    """View for the community page"""
    recent_comments = Comment.objects.all().order_by('-created_at')[:20]
    users = CustomUser.objects.all()[:10]  # Show some users
    
    context = {
        'comments': recent_comments,
        'users': users,
    }
    return render(request, 'community.html', context)

def settings_page(request):
    """View for the settings page"""
    return render(request, 'settings.html')