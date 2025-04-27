



from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import (
    Category, Subcategory, Technique,
    Comment, ExpertProfile, LiveSession,
    SessionRegistration, ChatMessage, Favorite
)

User = get_user_model()

class SubcategoryInline(admin.TabularInline):
    model = Subcategory
    extra = 1

class TechniqueInline(admin.TabularInline):
    model = Technique
    extra = 1

class SessionRegistrationInline(admin.TabularInline):
    model = SessionRegistration
    extra = 0

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    inlines = [SubcategoryInline]

@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'created_at', 'updated_at')
    list_filter = ('category',)
    search_fields = ('name', 'description')
    inlines = [TechniqueInline]

@admin.register(Technique)
class TechniqueAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'subcategory', 'difficulty', 'duration', 'time_of_day')
    list_filter = ('category', 'subcategory', 'difficulty', 'time_of_day')
    search_fields = ('name', 'description', 'benefits')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'technique', 'created_at')
    list_filter = ('technique',)
    search_fields = ('content',)

@admin.register(ExpertProfile)
class ExpertProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'expertise', 'is_verified')
    list_filter = ('expertise', 'is_verified')
    search_fields = ('user__username', 'user__email', 'expertise')

# @admin.register(LiveSession)
# class LiveSessionAdmin(admin.ModelAdmin):
#     list_display = ('title', 'host', 'start_time', 'end_time', 'status')
#     list_filter = ('status', 'start_time')
#     search_fields = ('title', 'description', 'host__user__username')
#     readonly_fields = ('room_name',)
#     inlines = [SessionRegistrationInline]

#     def save_model(self, request, obj, form, change):
#         if not obj.room_name:
#             import uuid
#             obj.room_name = f"session_{uuid.uuid4().hex[:8]}"
#         super().save_model(request, obj, form, change)


@admin.register(LiveSession)
class LiveSessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'host', 'start_time', 'end_time', 'status', 'has_meet_link')
    list_filter = ('status', 'start_time')
    search_fields = ('title', 'description', 'host__user__username')
    readonly_fields = ('room_name',)
    inlines = [SessionRegistrationInline]
    
    def has_meet_link(self, obj):
        return bool(obj.google_meet_link)
    has_meet_link.boolean = True
    has_meet_link.short_description = "Has Meet Link"

    def save_model(self, request, obj, form, change):
        if not obj.room_name:
            import uuid
            obj.room_name = f"session_{uuid.uuid4().hex[:8]}"
        super().save_model(request, obj, form, change)

@admin.register(SessionRegistration)
class SessionRegistrationAdmin(admin.ModelAdmin):
    list_display = ('user', 'session', 'registered_at', 'attended')
    list_filter = ('attended', 'registered_at')
    search_fields = ('user__username', 'session__title')

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'session', 'message', 'timestamp')
    list_filter = ('timestamp', 'session')
    search_fields = ('user__username', 'message')

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'technique', 'created_at')
    list_filter = ('user',)
