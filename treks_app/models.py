from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.utils.html import mark_safe
from django.conf import settings
from ckeditor.fields import RichTextField
from PIL import Image, ImageEnhance
import bleach
import uuid
import mimetypes
import io
from io import BytesIO
import os
from django.template.defaultfilters import filesizeformat
from .supabase_client import supabase

class Visitor(models.Model):
    ip_address = models.GenericIPAddressField()
    session_id = models.CharField(max_length=255, blank=True, db_index=True)
    user_agent = models.CharField(max_length=255, blank=True)
    visit_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["visit_time"]),
            models.Index(fields=["ip_address"]),
        ]

    def __str__(self):
        return f"{self.ip_address} @ {self.visit_time}"


def validate_image_file_extension(value):
    """
    Validate image file extension, size, and actual image content using Pillow.
    """

    VALID_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in VALID_EXTENSIONS:
        raise ValidationError(
            f"Unsupported file extension. Allowed: {', '.join(VALID_EXTENSIONS)}"
        )
    if value.size > MAX_FILE_SIZE:
        raise ValidationError(
            f"File size too large. Max size is {filesizeformat(MAX_FILE_SIZE)}."
        )
    try:
        value.seek(0)
        img = Image.open(value)
        img.verify()  
    except Exception:
        raise ValidationError("Uploaded file is not a valid image.")
    finally:
        value.seek(0) 

class Contact(models.Model):
    """Store contact form submissions."""
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    mobile = models.CharField(max_length=20)
    user_type = models.CharField(max_length=50, blank=True, null=True)
    comment = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.name} - {self.email}"
    


class Blog(models.Model):
    """Blog articles with watermarked images stored in Supabase."""
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    content = RichTextField()
    excerpt = models.TextField(max_length=300, blank=True, help_text="Short description for blog listings")
    image = models.ImageField(upload_to='blogs/', validators=[validate_image_file_extension], blank=True, null=True)
    original_image = models.ImageField(upload_to='blogs/originals/', validators=[validate_image_file_extension], blank=True, null=True)
    image_url = models.URLField(blank=True, null=True, editable=False)
    original_image_url = models.URLField(blank=True, null=True, editable=False)
    author = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def add_watermark(self, image_file):
        """Add centered watermark with low transparency"""
        image = Image.open(image_file).convert("RGBA")
        watermark = Image.open("static/images/R-logo.webp").convert("RGBA")  # your watermark logo

        # Resize watermark to 10% of image width
        w_ratio = int(image.width * 0.10)
        watermark = watermark.resize((w_ratio, int(watermark.height * (w_ratio / watermark.width))))

        # Reduce watermark transparency (light transparency)
        alpha = watermark.split()[3]
        alpha = ImageEnhance.Brightness(alpha).enhance(0.80)
        watermark.putalpha(alpha)

        # Position watermark
        x = (image.width - watermark.width) // 2
        y = (image.height - watermark.height) // 2
        image.paste(watermark, (x, y), watermark)

        # Save as WebP in memory
        output = BytesIO()
        image.convert("RGB").save(output, format="WEBP")
        output.seek(0)
        return output

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        bucket, folder = supabase.storage.from_("blogs"), "blogs"

        if self.image:
            if not self.original_image:
                original_file_name = f"{uuid.uuid4()}.webp"
                original_path = f"{folder}/originals/{original_file_name}"
                
                self.image.seek(0)
                file_content = BytesIO(self.image.read())
                
                bucket.upload(original_path, file_content.getvalue(), {"content-type": "image/webp"})
                self.original_image.name = original_path
                self.original_image_url = bucket.get_public_url(original_path)

            # Apply watermark
            self.image.seek(0)
            watermarked_image = self.add_watermark(self.image)
            file_name = f"{uuid.uuid4()}.webp"
            path = f"{folder}/{file_name}"
            bucket.upload(path, watermarked_image.read(), {"content-type": "image/webp"})
            self.image_url = bucket.get_public_url(path)
            self.image.name = file_name  

        else:
            # Remove images if cleared
            base_url = bucket.get_public_url("").rstrip("/") + "/"
            if self.image_url:
                file_path = self.image_url.replace(base_url, "", 1)
                bucket.remove([file_path])
            if self.original_image_url:
                original_path = self.original_image_url.replace(base_url, "", 1)
                bucket.remove([original_path])
            self.image = None
            self.original_image = None
            self.image_url = None
            self.original_image_url = None

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog_detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.title


class TrekCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Trek Categories"
    
    def __str__(self):
        return self.name

class TrekOrganizer(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    logo = models.ImageField(upload_to='organizers/', validators=[validate_image_file_extension])
    website = models.URLField(blank=True)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)
    is_verified = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name

class Trek(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('moderate', 'Moderate'),
        ('difficult', 'Difficult'),
        ('extreme', 'Extreme'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    short_description = models.TextField(max_length=300, blank=True)
    image = models.ImageField(upload_to='treks/', validators=[validate_image_file_extension])
    additional_images = models.ManyToManyField('TrekImage', blank=True, related_name='trek_images')
    category = models.ForeignKey(TrekCategory, on_delete=models.CASCADE, related_name='treks')
    organizer = models.ForeignKey(TrekOrganizer, on_delete=models.CASCADE, related_name='treks')
    duration = models.CharField(max_length=50, help_text="e.g., '2 days, 1 night'")
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    location = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('trek_detail', kwargs={'slug': self.slug})


class Testimonial(models.Model):
    name = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='testimonials/', blank=True, null=True, validators=[validate_image_file_extension])
    trek = models.ForeignKey(Trek, on_delete=models.SET_NULL, null=True, blank=True, related_name='testimonials')
    trek_name = models.CharField(max_length=200, blank=True, help_text="Only required if trek is not selected")
    date = models.DateField()
    content = models.TextField()
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    is_featured = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        # Sanitize content before saving to prevent XSS
        self.content = bleach.clean(self.content, tags=[], attributes={}, strip=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.trek or self.trek_name}"

class FAQ(models.Model):
    CATEGORY_CHOICES = [
        ('booking', 'Booking & Payment'),
        ('treks', 'Treks & Activities'),
        ('safety', 'Safety & Equipment'),
        ('Cancellation & Refund', 'Cancellation & Refund'),
        ('Payment-Related', 'Payment-Related'),
        ('Customer-support', 'Customer-Support'),
    ]
    
    question = models.CharField(max_length=300)
    answer = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='general')
    order = models.PositiveIntegerField(default=0, help_text="Order of display")
    
    class Meta:
        ordering = ['category', 'order']
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"
    
    def __str__(self):
        return self.question

class SafetyTip(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    icon = models.ImageField(upload_to='safety_icons/', blank=True, null=True, validators=[validate_image_file_extension])
    order = models.PositiveIntegerField(default=0, help_text="Order of display")
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.title

class TeamMember(models.Model):
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    bio = models.TextField()
    photo = models.ImageField(upload_to='team/', validators=[validate_image_file_extension])
    email = models.EmailField(blank=True)
    linkedin = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=0, help_text="Order of display")
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.name} - {self.position}"

class HomepageBanner(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    image = models.ImageField(upload_to='banners/', validators=[validate_image_file_extension])
    button_text = models.CharField(max_length=50, blank=True)
    button_url = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, help_text="Order of display")
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.title

class SocialMedia(models.Model):
    platform = models.CharField(max_length=50)
    url = models.URLField()
    icon = models.ImageField(upload_to='social_icons/', blank=True, null=True, validators=[validate_image_file_extension])
    order = models.PositiveIntegerField(default=0, help_text="Order of display")
    
    class Meta:
        ordering = ['order']
        verbose_name_plural = "Social Media Links"
    
    def __str__(self):
        return self.platform

class ContactInfo(models.Model):
    company_name = models.CharField(max_length=200)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    map_url = models.URLField(blank=True, help_text="Google Maps URL")
    
    class Meta:
        verbose_name_plural = "Contact Information"
    
    def __str__(self):
        return self.company_name


class WhatsNew(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to="whatsnew/", blank=True, null=True)
    image_url = models.URLField(blank=True, null=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        bucket, folder = supabase.storage.from_("blogs"), "whatsnew"

        if self.image:
            ext = self.image.name.split('.')[-1].lower()
            file_name = f"{uuid.uuid4()}.{ext}"
            path = f"{folder}/{file_name}"

            # Compress image before upload
            img = Image.open(self.image)
            img_io = io.BytesIO()
            if ext in ["jpg", "jpeg"]:
                img.save(img_io, format="JPEG", optimize=True, quality=70)  # adjust quality
            elif ext == "png":
                img.save(img_io, format="PNG", optimize=True)
            else:
                img.save(img_io, format=img.format)

            img_io.seek(0)

            mime, _ = mimetypes.guess_type(self.image.name)
            if not mime:
                mime = "application/octet-stream"

            bucket.upload(path, img_io.getvalue(), {"content-type": mime})
            self.image_url = bucket.get_public_url(path)
            self.image.name = file_name  

        elif not self.image and self.image_url:
            base_url = bucket.get_public_url("").rstrip("/") + "/"
            file_path = self.image_url.replace(base_url, "", 1)
            bucket.remove([file_path])
            self.image = None
            self.image_url = None

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class TopTrek(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to="toptreks/", blank=True, null=True)
    image_url = models.URLField(blank=True, null=True, editable=False)

    def save(self, *args, **kwargs):
        bucket, folder = supabase.storage.from_("blogs"), "toptreks"

        if self.image:
            ext = self.image.name.split('.')[-1].lower()
            file_name = f"{uuid.uuid4()}.{ext}"
            path = f"{folder}/{file_name}"

            # Compress image before upload
            img = Image.open(self.image)
            img_io = io.BytesIO()
            if ext in ["jpg", "jpeg"]:
                img.save(img_io, format="JPEG", optimize=True, quality=70)
            elif ext == "png":
                img.save(img_io, format="PNG", optimize=True)
            else:
                img.save(img_io, format=img.format)

            img_io.seek(0)

            mime, _ = mimetypes.guess_type(self.image.name)
            if not mime:
                mime = "application/octet-stream"

            bucket.upload(path, img_io.getvalue(), {"content-type": mime})
            self.image_url = bucket.get_public_url(path)
            self.image.name = file_name  

        elif not self.image and self.image_url:
            base = bucket.get_public_url("").rstrip("/") + "/"
            bucket.remove([self.image_url.replace(base, "", 1)])
            self.image = None
            self.image_url = None

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    


class TermsAndConditions(models.Model):
    title = models.CharField(max_length=255, default="Terms and Conditions")
    content = RichTextField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} (Last updated: {self.updated_at.strftime('%Y-%m-%d')})"

    def content_preview(self):
        return mark_safe(self.content[:300] + "...")
    
class Operator(models.Model):
    name = models.CharField(max_length=200, unique=True)
    def __str__(self): return self.name

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    def __str__(self): return self.name

class TrekPoint(models.Model):
    name = models.CharField(max_length=200)
    def __str__(self): return self.name

class TrekList(models.Model):
    id = models.SlugField(primary_key=True, editable=False)
    name = models.CharField(max_length=200)
    state = models.CharField(max_length=100, blank=True, null=True)

    is_pinned = models.BooleanField(default=False)
    pin_priority = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Lower number = higher priority (1 comes first)"
    )

    image = models.CharField(max_length=500, blank=True, null=True)
    hero_image = models.CharField(max_length=500, blank=True, null=True)
    duration_days = models.CharField(max_length=100, blank=True, null=True)

    price_start = models.PositiveIntegerField(blank=True, null=True)
    currency = models.CharField(max_length=10, default="INR")
    operating_days = models.CharField(max_length=200, blank=True, null=True)

    tags = models.ManyToManyField(Tag, blank=True)
    operators = models.ManyToManyField(Operator, blank=True)
    trek_points = models.ManyToManyField(TrekPoint, blank=True)

    short_desc = models.TextField(blank=True, null=True)
    highlights = models.TextField(blank=True, null=True)
    activities = models.TextField(
        blank=True,
        null=True,
        help_text="Comma-separated values. Example: Trekking, Camping, Bonfire"
    )
    related_treks = models.ManyToManyField('self', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.id:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1

            while TrekList.objects.filter(id=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.id = slug

        super().save(*args, **kwargs)

    @property
    def activities_list(self):
        if not self.activities:
            return []
        return [a.strip() for a in self.activities.split(",") if a.strip()]

    def __str__(self):
        return self.name

 
class TrekImage(models.Model):
    trek = models.ForeignKey(
        TrekList,
        related_name="images",
        on_delete=models.CASCADE
    )

    # Used ONLY for upload input (admin/form)
    image = models.ImageField(
        upload_to="trek_images/",
        validators=[validate_image_file_extension],
        blank=True,
        null=True
    )

    # Actual frontend-consumed field
    image_url = models.URLField(
        blank=True,
        null=True,
        editable=False
    )

    caption = models.CharField(max_length=200, blank=True)

    def save(self, *args, **kwargs):
        bucket = supabase.storage.from_("blogs")
        folder = "trek_images"

        # Upload new image
        if self.image:
            ext = self.image.name.split(".")[-1].lower()
            file_name = f"{uuid.uuid4()}.{ext}"
            path = f"{folder}/{file_name}"

            # Compress image
            img = Image.open(self.image)
            img_io = io.BytesIO()

            if ext in ["jpg", "jpeg"]:
                img.save(img_io, format="JPEG", optimize=True, quality=70)
                mime = "image/jpeg"
            elif ext == "png":
                img.save(img_io, format="PNG", optimize=True)
                mime = "image/png"
            else:
                img.save(img_io, format=img.format)
                mime = mimetypes.guess_type(self.image.name)[0] or "application/octet-stream"

            img_io.seek(0)

            # Remove old image if updating
            if self.image_url:
                base = bucket.get_public_url("").rstrip("/") + "/"
                old_path = self.image_url.replace(base, "", 1)
                bucket.remove([old_path])

            # Upload to Supabase
            bucket.upload(path, img_io.getvalue(), {"content-type": mime})
            self.image_url = bucket.get_public_url(path)

            # Prevent Django from storing the file locally
            self.image = None

        super().save(*args, **kwargs)

    def __str__(self):
        return self.caption or f"{self.trek.name} - Image"