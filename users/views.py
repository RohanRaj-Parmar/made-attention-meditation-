from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
# For Django's built-in email functionality
from django.core.mail import send_mail
# For SendGrid Django integration
from django.core.mail import EmailMessage
# If using SendGrid
from django.core.mail import send_mail
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import traceback




from .forms import (
    CustomUserCreationForm, 
    CustomAuthenticationForm, 
    OTPLoginForm, 
    VerifyOTPForm,
    CustomPasswordResetForm,
    CustomSetPasswordForm
)
from .models import CustomUser, OTP


def register_view(request):
    if request.user.is_authenticated:
        return redirect('users:login')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Generate verification OTP
            otp_obj = OTP.generate_otp(user, purpose='verification')
            # Send OTP to user's email
            send_otp_email(user.email, otp_obj.otp, 'Account Verification')
            
            login(request, user)
            messages.success(request, "Registration successful! Please verify your email.")
            return redirect('meditation:home')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'users/register.html', {'form': form})


def front_page_view(request):
    if request.user.is_authenticated:
        return redirect('meditation:home')  # Redirect logged-in users to home
    return render(request, 'front.html')  # Show front page only to non-logged-in users


def login_view(request):
    if request.user.is_authenticated:
        return redirect('meditation:home')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, "You have been logged in successfully!")
                return redirect('meditation:home')
            else:
                messages.error(request, "Invalid email or password.")
        else:
            messages.error(request, "Invalid email or password.")
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'users/login.html', {
        'form': form,
        'otp_form': OTPLoginForm()
    })


# def logout_view(request):
#     logout(request)
#     messages.success(request, "You have been logged out successfully!")
#     return redirect('meditation:home')


def logout_view(request):
    logout(request)
    messages.error(request, "You have been logged out successfully!")  # This will display as alert-danger
    return redirect('meditation:home')

def otp_login_request(request):
    if request.method == 'POST':
        form = OTPLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            try:
                user = CustomUser.objects.get(email=email)
                # Generate OTP for login
                otp_obj = OTP.generate_otp(user, purpose='login')
                # Send OTP email
                send_otp_email(user.email, otp_obj.otp, 'Login')
                
                # Store email in session for verification step
                request.session['otp_email'] = email
                request.session['otp_purpose'] = 'login'
                
                messages.success(request, "OTP has been sent to your email!")
                return redirect('verify_otp')
            except CustomUser.DoesNotExist:
                messages.error(request, "No account found with this email address.")
                return redirect('login')
    
    return redirect('login')


def verify_otp_view(request):
    email = request.session.get('otp_email')
    purpose = request.session.get('otp_purpose')
    
    if not email or not purpose:
        messages.error(request, "Invalid session. Please try again.")
        return redirect('login')
    
    if request.method == 'POST':
        form = VerifyOTPForm(request.POST)
        if form.is_valid():
            otp_entered = form.cleaned_data.get('otp')
            try:
                user = CustomUser.objects.get(email=email)
                # Get the latest unused OTP for this user and purpose
                otp_obj = OTP.objects.filter(
                    user=user,
                    purpose=purpose,
                    is_verified=False,
                    expires_at__gt=timezone.now()
                ).latest('created_at')
                
                if otp_obj.otp == otp_entered:
                    # Mark OTP as verified
                    otp_obj.is_verified = True
                    otp_obj.save()
                    
                    # Handle based on purpose
                    if purpose == 'login':
                        login(request, user)
                        messages.success(request, "Login successful!")
                        return redirect('home')
                    elif purpose == 'password_reset':
                        request.session['reset_user_id'] = user.id
                        return redirect('reset_password')
                    elif purpose == 'verification':
                        user.is_active = True
                        user.save()
                        messages.success(request, "Email verified successfully!")
                        return redirect('home')
                else:
                    messages.error(request, "Invalid OTP. Please try again.")
            except (CustomUser.DoesNotExist, OTP.DoesNotExist):
                messages.error(request, "Invalid OTP or OTP expired. Please try again.")
        else:
            messages.error(request, "Please enter a valid 6-digit OTP.")
    
    form = VerifyOTPForm()
    return render(request, 'users/verify_otp.html', {
        'form': form,
        'email': email,
        'purpose': purpose
    })

def otp_login_view(request):
    email = request.POST.get('email')
    try:
        user = CustomUser.objects.get(email=email)
        otp = OTP.generate_otp(user, 'login')
        send_otp_email(email, otp.otp, 'Login')
        request.session['login_email'] = email
        return JsonResponse({'success': True, 'message': 'OTP sent to your email'})
    except CustomUser.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'No account found with that email'})



def forgot_password_view(request):
    if request.user.is_authenticated:
        return redirect('meditation:home')
    
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            try:
                user = CustomUser.objects.get(email=email)
                # Generate OTP for password reset
                otp_obj = OTP.generate_otp(user, purpose='password_reset')
                # Send OTP email
                send_otp_email(user.email, otp_obj.otp, 'Password Reset')
                
                # Store email in session for verification step
                request.session['otp_email'] = email
                request.session['otp_purpose'] = 'password_reset'
                
                messages.success(request, "Password reset OTP has been sent to your email!")
                return redirect('users:verify_otp')
            except CustomUser.DoesNotExist:
                # For security reasons, don't reveal that the email doesn't exist
                messages.success(request, "If an account exists with this email, a password reset OTP has been sent.")
                return redirect('users:login')
    else:
        form = CustomPasswordResetForm()
    
    return render(request, 'users/forgot_password.html', {'form': form})


def reset_password_view(request):
    user_id = request.session.get('reset_user_id')
    if not user_id:
        messages.error(request, "Invalid session. Please try again.")
        return redirect('forgot_password')
    
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        messages.error(request, "User not found. Please try again.")
        return redirect('forgot_password')
    
    if request.method == 'POST':
        form = CustomSetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            # Clear session data
            del request.session['reset_user_id']
            del request.session['otp_email']
            del request.session['otp_purpose']
            
            messages.success(request, "Your password has been reset successfully! You can now login with your new password.")
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CustomSetPasswordForm(user)
    
    return render(request, 'users/reset_password.html', {'form': form})


def verify_otp_ajax(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        otp_entered = request.POST.get('otp')
        email = request.session.get('otp_email')
        purpose = request.session.get('otp_purpose')
        
        if not email or not purpose or not otp_entered:
            return JsonResponse({'valid': False, 'message': 'Invalid request'})
        
        try:
            user = CustomUser.objects.get(email=email)
            otp_obj = OTP.objects.filter(
                user=user,
                purpose=purpose,
                is_verified=False,
                expires_at__gt=timezone.now()
            ).latest('created_at')
            
            if otp_obj.otp == otp_entered:
                return JsonResponse({'valid': True})
            else:
                return JsonResponse({'valid': False, 'message': 'Invalid OTP'})
        except (CustomUser.DoesNotExist, OTP.DoesNotExist):
            return JsonResponse({'valid': False, 'message': 'Invalid OTP or OTP expired'})
    
    return JsonResponse({'valid': False, 'message': 'Invalid request'})
@login_required
def settings_page(request):
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        if form_type == 'profile':
            # Handle profile form submission
            email = request.POST.get('email')
            bio = request.POST.get('bio')
            profile_picture = request.FILES.get('profile_picture')
            
            # Update user email
            if email and email != request.user.email:
                request.user.email = email
                request.user.save()
            
            # Make sure user has a profile
            if not hasattr(request.user, 'profile'):
                # Create profile model if it doesn't exist
                from users.models import Profile
                Profile.objects.create(user=request.user)
            
            # Update profile fields
            if bio is not None:
                request.user.profile.bio = bio
            
            if profile_picture:
                request.user.profile.profile_picture = profile_picture
            
            request.user.profile.save()
            messages.success(request, 'Your profile has been updated successfully!')
            
        elif form_type == 'preferences':
            # Handle preferences form submission
            theme = request.POST.get('theme')
            language = request.POST.get('language')
            
            # Make sure user has a profile
            if not hasattr(request.user, 'profile'):
                # Create profile model if it doesn't exist
                from users.models import Profile
                Profile.objects.create(user=request.user)
            
            # Update theme and language preferences
            if theme:
                request.user.profile.theme = theme
            
            if language:
                request.user.profile.language = language
            
            request.user.profile.save()
            messages.success(request, 'Your preferences have been updated successfully!')
            
        elif form_type == 'notifications':
            # Handle notifications form submission
            email_notifications = request.POST.get('email_notifications') == 'on'
            comment_notifications = request.POST.get('comment_notifications') == 'on'
            newsletter = request.POST.get('newsletter') == 'on'
            
            # Make sure user has a profile
            if not hasattr(request.user, 'profile'):
                # Create profile model if it doesn't exist
                from users.models import Profile
                Profile.objects.create(user=request.user)
            
            # Update notification preferences
            request.user.profile.email_notifications = email_notifications
            request.user.profile.comment_notifications = comment_notifications
            request.user.profile.newsletter = newsletter
            request.user.profile.save()
            messages.success(request, 'Your notification settings have been updated successfully!')
            
        elif form_type == 'security':
            # Handle password change
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if not current_password or not new_password or not confirm_password:
                messages.error(request, 'Please fill in all password fields!')
            elif new_password != confirm_password:
                messages.error(request, 'New passwords do not match!')
            else:
                # Check if current password is correct
                if request.user.check_password(current_password):
                    request.user.set_password(new_password)
                    request.user.save()
                    update_session_auth_hash(request, request.user)  # Keep user logged in
                    messages.success(request, 'Your password has been changed successfully!')
                else:
                    messages.error(request, 'Current password is incorrect!')
        
        # Redirect back to settings page after processing any form
        return redirect('settings')
    
    # For GET requests, just display the settings page
    return render(request, 'settings.html')

@login_required
def settings(request):
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        if form_type == 'profile':
            # Handle profile form submission
            email = request.POST.get('email')
            bio = request.POST.get('bio')
            profile_picture = request.FILES.get('profile_picture')
            
            # Update user email
            if email and email != request.user.email:
                request.user.email = email
                request.user.save()
            
            # Update profile
            profile = request.user.profile
            if bio is not None:  # Allow empty bio
                profile.bio = bio
            
            if profile_picture:
                profile.profile_picture = profile_picture
                
            profile.save()
            messages.success(request, 'Profile updated successfully!')
            
        elif form_type == 'preferences':
            # Handle preferences form
            theme = request.POST.get('theme')
            language = request.POST.get('language')
            
            profile = request.user.profile
            profile.theme = theme
            profile.language = language
            profile.save()
            
            messages.success(request, 'Preferences updated successfully!')
            
        elif form_type == 'notifications':
            # Handle notification settings
            email_notifications = 'email_notifications' in request.POST
            comment_notifications = 'comment_notifications' in request.POST
            newsletter = 'newsletter' in request.POST
            
            profile = request.user.profile
            profile.email_notifications = email_notifications
            profile.comment_notifications = comment_notifications
            profile.newsletter = newsletter
            profile.save()
            
            messages.success(request, 'Notification settings updated successfully!')
            
        elif form_type == 'security':
            # Handle password change
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            user = request.user
            
            if not user.check_password(current_password):
                messages.error(request, 'Current password is incorrect!')
            elif new_password != confirm_password:
                messages.error(request, 'New passwords do not match!')
            elif len(new_password) < 8:
                messages.error(request, 'Password must be at least 8 characters long!')
            else:
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Password changed successfully! Please log in again.')
                return redirect('users:login')
        
        # Redirect to the same page to prevent form resubmission
        return redirect('meditation:settings')
    
    return render(request, 'setting.html')

def send_otp_email(email, otp, purpose):
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    
    subject_map = {
        'Login': 'Login OTP for Meditation App',
        'Password Reset': 'Password Reset OTP for Meditation App',
        'Account Verification': 'Verify Your Meditation App Account'
    }
    
    message_map = {
        'Login': f'Your OTP for logging into the Meditation App is: {otp}. This OTP will expire in 10 minutes.',
        'Password Reset': f'Your OTP for resetting your Meditation App password is: {otp}. This OTP will expire in 10 minutes.',
        'Account Verification': f'Your OTP for verifying your Meditation App account is: {otp}. This OTP will expire in 10 minutes.'
    }
    
    subject = subject_map.get(purpose, f'{purpose} OTP for Meditation App')
    message_content = message_map.get(purpose, f'Your OTP for {purpose.lower()} is: {otp}. This OTP will expire in 10 minutes.')
    
    try:
        message = Mail(
            from_email=settings.DEFAULT_FROM_EMAIL,
            to_emails=email,
            subject=subject,
            plain_text_content=message_content)
        
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        
        print(f"SendGrid Response Status Code: {response.status_code}")
        return response.status_code == 202
    except Exception as e:
        import traceback
        print(f"Error sending email: {e}")
        print(traceback.format_exc())
        return False
    

def send_otp_email(email, otp, purpose):
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    
    subject_map = {
        'Login': 'Login OTP for Meditation App',
        'Password Reset': 'Password Reset OTP for Meditation App',
        'Account Verification': 'Verify Your Meditation App Account'
    }
    
    message_map = {
        'Login': f'Your OTP for logging into the Meditation App is: {otp}. This OTP will expire in 10 minutes.',
        'Password Reset': f'Your OTP for resetting your Meditation App password is: {otp}. This OTP will expire in 10 minutes.',
        'Account Verification': f'Your OTP for verifying your Meditation App account is: {otp}. This OTP will expire in 10 minutes.'
    }
    
    subject = subject_map.get(purpose, f'{purpose} OTP for Meditation App')
    message_content = message_map.get(purpose, f'Your OTP for {purpose.lower()} is: {otp}. This OTP will expire in 10 minutes.')
    
    # First try SendGrid
    try:
        message = Mail(
            from_email=settings.DEFAULT_FROM_EMAIL,
            to_emails=email,
            subject=subject,
            plain_text_content=message_content)
        
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        
        print(f"SendGrid Response Status Code: {response.status_code}")
        return response.status_code == 202
    except Exception as e:
        import traceback
        print(f"SendGrid Error: {e}")
        print(traceback.format_exc())
        
        # Fallback to Django's send_mail
        try:
            send_mail(
                subject=subject,
                message=message_content,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
            )
            print("Email sent successfully using Django's send_mail")
            return True
        except Exception as e2:
            print(f"Django send_mail Error: {e2}")
            print(traceback.format_exc())
            return False

def test_email_view(request):
    success = send_mail(
        'Test Email from Django',
        'This is a test email from your Django application.',
        settings.DEFAULT_FROM_EMAIL,
        ['your-test-email@gmail.com'],  # Your email to receive the test
        fail_silently=False,
    )
    
    if success:
        return ("Test email sent successfully!")
    else:
        return HttpResponse("Failed to send test email. Check server logs.")
# Helper function to send OTP emails
# def send_otp_email(email, otp, purpose):
#     subject_map = {
#         'Login': 'Login OTP for Meditation App',
#         'Password Reset': 'Password Reset OTP for Meditation App',
#         'Account Verification': 'Verify Your Meditation App Account'
#     }
    
#     message_map = {
#         'Login': f'Your OTP for logging into the Meditation App is: {otp}. This OTP will expire in 10 minutes.',
#         'Password Reset': f'Your OTP for resetting your Meditation App password is: {otp}. This OTP will expire in 10 minutes.',
#         'Account Verification': f'Your OTP for verifying your Meditation App account is: {otp}. This OTP will expire in 10 minutes.'
#     }
    
#     subject = subject_map.get(purpose, f'{purpose} OTP for Meditation App')
#     message = message_map.get(purpose, f'Your OTP for {purpose.lower()} is: {otp}. This OTP will expire in 10 minutes.')
    
#     try:
#         send_mail(
#             subject=subject,
#             message=message,
#             from_email=settings.EMAIL_HOST_USER,
#             recipient_list=[email],
#             fail_silently=False,
#         )
#         return True
#     except Exception as e:
#         print(f"Error sending email: {e}")
#         return False
