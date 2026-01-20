from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from django.utils import timezone
from django.utils.safestring import mark_safe

admin.site.site_header = "Aorbo Treks Admin"
admin.site.site_title = "Aorbo Treks Admin Pannel"
admin.site.index_title = "Dashboard"

from .models import (
    Contact, Blog, TrekCategory, TrekOrganizer, Trek, TrekImage,
    Testimonial, FAQ, SafetyTip, TeamMember, HomepageBanner,
    SocialMedia, ContactInfo, WhatsNew, TopTrek,
    TrekList,Visitor, TermsAndConditions, Operator, Tag, TrekPoint 
)   

@admin.register(WhatsNew)
class WhatsNewAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'image_preview')
    readonly_fields = ('image_preview',)
    fields = ('title', 'content', 'image', 'image_preview', 'created_at')
    readonly_fields = ('image_preview', 'created_at')

    def image_preview(self, obj):
        if obj.image_url:
            return format_html('<img src="{}" width="100" />', obj.image_url)
        return "No image"
    image_preview.short_description = "Image Preview"

    
@admin.register(TopTrek)    
class TopTrekAdmin(admin.ModelAdmin):
    list_display = ('name', 'image_preview')
    readonly_fields = ('image_preview',)
    fields = ('name', 'description', 'image', 'image_preview')

    def image_preview(self, obj):
        if obj.image_url:
            return format_html('<img src="{}" width="100" />', obj.image_url)
        return "No image"
    image_preview.short_description = "Image Preview"

# Register your models here.
@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'mobile', 'user_type', 'created_at')
    list_filter = ('user_type', 'created_at')
    search_fields = ('name', 'email', 'mobile', 'comment')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'

@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at', 'is_featured', 'image_preview')
    list_filter = ('is_featured', 'created_at')
    search_fields = ('title', 'content', 'author')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'image_preview')
    date_hierarchy = 'created_at'
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'author', 'is_featured')
        }),
        ('Content', {
            'fields': ('content', 'excerpt')
        }),
        ('Image', {
            'fields': ('image', 'image_preview')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" />', obj.image.url)
        return "-"
    image_preview.short_description = 'Image Preview'

@admin.register(TrekCategory)
class TrekCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')

class TrekImageInline(admin.TabularInline):
    model = Trek.additional_images.through
    extra = 1

@admin.register(TrekOrganizer)
class TrekOrganizerAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_email', 'contact_phone', 'is_verified', 'logo_preview')
    list_filter = ('is_verified',)
    search_fields = ('name', 'description', 'contact_email')
    
    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="50" />', obj.logo.url)
        return "-"
    logo_preview.short_description = 'Logo'

@admin.register(Trek)
class TrekAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'organizer', 'difficulty', 'price', 'is_featured', 'image_preview')
    list_filter = ('category', 'difficulty', 'is_featured', 'created_at')
    search_fields = ('title', 'description', 'location')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'image_preview')
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'category', 'organizer', 'is_featured')
        }),
        ('Details', {
            'fields': ('description', 'short_description', 'duration', 'difficulty', 'location')
        }),
        ('Pricing', {
            'fields': ('price', 'discount_price')
        }),
        ('Image', {
            'fields': ('image', 'image_preview')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" />', obj.image.url)
        return "-"
    image_preview.short_description = 'Image Preview'

@admin.register(TrekImage)
class TrekImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'caption', 'image_preview')
    search_fields = ('caption',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" />', obj.image.url)
        return "-"
    image_preview.short_description = 'Image Preview'

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name', 'trek_display', 'rating', 'date', 'is_featured', 'photo_preview')
    list_filter = ('rating', 'is_featured', 'date')
    search_fields = ('name', 'content', 'trek_name')
    readonly_fields = ('photo_preview',)
    
    def trek_display(self, obj):
        return obj.trek.title if obj.trek else obj.trek_name
    trek_display.short_description = 'Trek'
    
    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="50" />', obj.photo.url)
        return "-"
    photo_preview.short_description = 'Photo'

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'order')
    list_filter = ('category',)
    search_fields = ('question', 'answer')
    list_editable = ('order',)

@admin.register(SafetyTip)
class SafetyTipAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'icon_preview')
    search_fields = ('title', 'content')
    list_editable = ('order',)
    
    def icon_preview(self, obj):
        if obj.icon:
            return format_html('<img src="{}" width="30" />', obj.icon.url)
        return "-"
    icon_preview.short_description = 'Icon'

@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'order', 'photo_preview')
    search_fields = ('name', 'position', 'bio')
    list_editable = ('order',)
    
    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="50" />', obj.photo.url)
        return "-"
    photo_preview.short_description = 'Photo'

@admin.register(HomepageBanner)
class HomepageBannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'order', 'image_preview')
    list_filter = ('is_active',)
    search_fields = ('title', 'subtitle')
    list_editable = ('is_active', 'order')
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" />', obj.image.url)
        return "-"
    image_preview.short_description = 'Image Preview'

@admin.register(SocialMedia)
class SocialMediaAdmin(admin.ModelAdmin):
    list_display = ('platform', 'url', 'order', 'icon_preview')
    search_fields = ('platform',)
    list_editable = ('order',)
    
    def icon_preview(self, obj):
        if obj.icon:
            return format_html('<img src="{}" width="30" />', obj.icon.url)
        return "-"
    icon_preview.short_description = 'Icon'

@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'email', 'phone')
    search_fields = ('company_name', 'address', 'email', 'phone')

@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = ("ip_address", "session_id", "user_agent", "visit_time")
    list_filter = ("visit_time",)
    date_hierarchy = "visit_time"
    search_fields = ("ip_address", "session_id", "user_agent")
    readonly_fields = ("ip_address", "session_id", "user_agent", "visit_time")

    change_list_template = "admin/visitor_changelist.html"

    def changelist_view(self, request, extra_context=None):
        from django.db.models.functions import TruncDate
        today =  timezone.localdate()
        qs = Visitor.objects.all()
        total_visitors = qs.count()
        unique_sessions = qs.values("session_id").distinct().count()
        today_unique = qs.filter(visit_time__date=today).values("session_id").distinct().count()
        daily_unique = (
            qs.annotate(day=TruncDate("visit_time"))
              .values("day")
              .annotate(unique=Count("session_id", distinct=True))
              .order_by("-day")[:14]
        )
        extra = {
            "total_visitors": total_visitors,
            "unique_sessions": unique_sessions,
            "today_unique": today_unique,
            "daily_unique": list(daily_unique),
        }
        extra_context = {**(extra_context or {}), **extra}
        return super().changelist_view(request, extra_context=extra_context)

@admin.register(TermsAndConditions)
class TermsAndConditionsAdmin(admin.ModelAdmin):
    list_display = ('title', 'updated_at', 'content_preview')
    readonly_fields = ('updated_at',)

    def content_preview(self, obj):
        return mark_safe(obj.content[:100] + '...')  if obj.content else "-"
    content_preview.short_description = 'Content Preview'

# @admin.register(TrekList)
# class TrekListAdmin(admin.ModelAdmin):

#     # LIST PAGE (table view)
#     list_display = (
#         'name',
#         'state',
#         'duration_days',
#         'price_start',
#         'currency',
#         'created_at'
#     )
#     list_filter = ('state', 'currency', 'created_at')
#     search_fields = ('name', 'state', 'short_desc')
#     ordering = ('-created_at',)
#     date_hierarchy = 'created_at'

#     # FORM PAGE (edit view)
#     readonly_fields = ('created_at', 'image_preview', 'hero_image_preview')

#     fieldsets = (
#         ("Basic Info", {
#             "fields": ('id', 'name', 'state')
#         }),
#         ("Images", {
#             "fields": ('image', 'image_preview', 'hero_image', 'hero_image_preview')
#         }),
#         ("Pricing & Duration", {
#             "fields": ('duration_days', 'price_start', 'currency', 'operating_days')
#         }),
#         ("Content", {
#             "fields": ('short_desc', 'highlights', 'activities')
#         }),
#         ("Relationships", {
#             "fields": ('tags', 'operators', 'trek_points', 'related_treks')
#         }),
#         ("Meta", {
#             "fields": ('created_at',),
#             "classes": ('collapse',)
#         }),
#     )

#     # Better UI for ManyToMany
#     filter_horizontal = ('tags', 'operators', 'trek_points', 'related_treks')

#     # -------- IMAGE PREVIEWS --------
#     def image_preview(self, obj):
#         if obj.image:
#             return format_html('<img src="{}" width="120" />', obj.image)
#         return "No image"

#     def hero_image_preview(self, obj):
#         if obj.hero_image:
#             return format_html('<img src="{}" width="200" />', obj.hero_image)
#         return "No hero image"

#     image_preview.short_description = "Image Preview"
#     hero_image_preview.short_description = "Hero Image Preview"

# @admin.register(TrekList)
# class TrekListAdmin(admin.ModelAdmin):

#     list_display = (
#         'name',
#         'state',
#         'duration_days',
#         'price_start',
#         'currency',
#         'created_at'
#     )
#     list_filter = ('state', 'currency', 'created_at')
#     search_fields = ('name', 'state', 'short_desc')
#     ordering = ('-created_at',)
#     date_hierarchy = 'created_at'

#     # ✅ ADD id here
#     readonly_fields = (
#         'id',
#         'created_at',
#         'image_preview',
#         'hero_image_preview'
#     )

#     fieldsets = (
#         ("Basic Info", {
#             # ✅ SAFE because id is readonly
#             "fields": ('id', 'name', 'state')
#         }),
#         ("Images", {
#             "fields": ('image', 'image_preview', 'hero_image', 'hero_image_preview')
#         }),
#         ("Pricing & Duration", {
#             "fields": ('duration_days', 'price_start', 'currency', 'operating_days')
#         }),
#         ("Content", {
#             "fields": ('short_desc', 'highlights', 'activities')
#         }),
#         ("Relationships", {
#             "fields": ('tags', 'operators', 'trek_points', 'related_treks')
#         }),
#         ("Meta", {
#             "fields": ('created_at',),
#             "classes": ('collapse',)
#         }),
#     )

#     filter_horizontal = ('tags', 'operators', 'trek_points', 'related_treks')

#     def image_preview(self, obj):
#         if obj.image:
#             return format_html('<img src="{}" width="120" />', obj.image)
#         return "No image"

#     def hero_image_preview(self, obj):
#         if obj.hero_image:
#             return format_html('<img src="{}" width="200" />', obj.hero_image)
#         return "No hero image"

#     image_preview.short_description = "Image Preview"
#     hero_image_preview.short_description = "Hero Image Preview"

from django.contrib import admin
from django.utils.html import format_html
from .models import TrekList


@admin.register(TrekList)
class TrekListAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'state',
        'is_pinned',        # 📌
        'pin_priority',     # 🔢
        'duration_days',
        'price_start',
        'currency',
        'created_at'
    )

    list_editable = (
        'is_pinned',
        'pin_priority'
    )

    list_filter = (
        'state',
        'currency',
        'is_pinned',
        'created_at'
    )

    ordering = ('pin_priority', '-created_at')
    search_fields = ('name', 'state', 'short_desc')
    date_hierarchy = 'created_at'

    readonly_fields = (
        'id',
        'created_at',
        'image_preview',
        'hero_image_preview'
    )

    fieldsets = (
        ("Basic Info", {
            "fields": ('id', 'name', 'state')
        }),

        ("📌 Pin Settings", {
            "fields": ('is_pinned', 'pin_priority'),
            "description": "Pinned treks appear first based on priority (1 = highest)"
        }),
       
        ("Pricing & Duration", {
            "fields": ('duration_days', 'price_start', 'currency', 'operating_days')
        }),

        ("Content", {
            "fields": ('short_desc', 'activities')
        }),

        ("Relationships", {
            "fields": ('tags', 'operators', 'trek_points', 'related_treks')
        }),

        ("Meta", {
            "fields": ('created_at',),
            "classes": ('collapse',)
        }),
    )

    filter_horizontal = ('tags', 'operators', 'trek_points', 'related_treks')

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="120" />', obj.image)
        return "No image"

    def hero_image_preview(self, obj):
        if obj.hero_image:
            return format_html('<img src="{}" width="200" />', obj.hero_image)
        return "No hero image"

    image_preview.short_description = "Image Preview"
    hero_image_preview.short_description = "Hero Image Preview"

    def save_model(self, request, obj, form, change):
        if not obj.is_pinned:
            obj.pin_priority = None
        super().save_model(request, obj, form, change)



@admin.register(Operator)
class OperatorAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(TrekPoint)
class TrekPointAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

