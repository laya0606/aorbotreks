from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.core.paginator import Paginator
import json
from django.urls import reverse
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from django.shortcuts import render
from treks_app.models import TrekList
from django.db.models import Q
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from datetime import datetime
import requests
from django.conf import settings
from itertools import chain
from django.db.models import Case, When, IntegerField
    
from .models import (
    Contact, Blog, TrekCategory, TrekOrganizer, Trek, 
    Testimonial, FAQ, SafetyTip, TeamMember, HomepageBanner,
    SocialMedia, ContactInfo,WhatsNew, TopTrek
)



def get_featured_treks():
    return TrekList.objects.annotate(
        pin_order=Case(
            When(is_pinned=True, then=0),
            default=1,
            output_field=IntegerField()
        )
    ).order_by(
        'pin_order',
        'pin_priority',
        '-created_at'
    )

from django.core.paginator import Paginator

def home(request):
    all_featured_treks = get_featured_treks()

    paginator = Paginator(all_featured_treks, 8)
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page_number)
    except Exception:
        page_obj = paginator.page(1)
    page_obj = paginator.get_page(page_number)
    featured_testimonials = Testimonial.objects.filter(is_featured=True)[:6]
    featured_blogs = Blog.objects.filter(is_featured=True)[:3]
    banners = HomepageBanner.objects.filter(is_active=True).order_by('order')
    faqs = FAQ.objects.all().order_by('category', 'order')
    whats_new = WhatsNew.objects.all().order_by('-created_at')[:5]
    top_treks = TopTrek.objects.all()[:6]

    faq_categories = {}
    for faq in faqs:
        faq_categories.setdefault(faq.category, []).append(faq)

    context = {
        'featured_treks': page_obj.object_list,
        'page_obj': page_obj,

        'featured_testimonials': featured_testimonials,
        'featured_blogs': featured_blogs,
        'banners': banners,
        'faq_categories': faq_categories,
        'whats_new': whats_new,
        'top_treks': top_treks,
    }

    return render(request, 'index.html', context)

def about(request):
    team_members = TeamMember.objects.all().order_by('order')
    context = {
        'team_members': team_members,
    }
    return render(request, 'about.html', context)

def blogs(request):
    all_blogs = Blog.objects.all().order_by('-created_at')[:6]
    paginator = Paginator(all_blogs, 6)  
    
    page_number = request.GET.get('page')
    blogs = paginator.get_page(page_number)
    
    context = {
        'blogs': blogs,
    }
    return render(request, 'blogs.html', context)

def blog_detail(request, slug):
    blog = get_object_or_404(Blog, slug=slug)
    recent_blogs = Blog.objects.exclude(id=blog.id).order_by('-created_at')[:3]
    
    context = {
        'blog': blog,
        'recent_blogs': recent_blogs,
    }
    return render(request, 'blog_detail.html', context)

def treks(request):
    category_id = request.GET.get('category')
    difficulty = request.GET.get('difficulty')
    
    all_treks = Trek.objects.all()
    
    # Apply filters if provided
    if category_id:
        all_treks = all_treks.filter(category_id=category_id)
    if difficulty:
        all_treks = all_treks.filter(difficulty=difficulty)
    
    # Get all categories for filter dropdown
    categories = TrekCategory.objects.all()
    
    paginator = Paginator(all_treks, 12)  # Show 12 treks per page
    page_number = request.GET.get('page')
    treks = paginator.get_page(page_number)
    
    context = {
        'treks': treks,
        'categories': categories,
        'selected_category': category_id,
        'selected_difficulty': difficulty,
        'difficulty_choices': Trek.DIFFICULTY_CHOICES,
    }
    return render(request, 'treks.html', context)

def trek_detail(request, slug):
    trek = get_object_or_404(Trek, slug=slug)
    testimonials = trek.testimonials.all()
    similar_treks = Trek.objects.filter(category=trek.category).exclude(id=trek.id)[:3]
    
    context = {
        'trek': trek,
        'testimonials': testimonials,
        'similar_treks': similar_treks,
    }
    return render(request, 'trek_detail.html', context)

def safety(request):
    safety_tips = SafetyTip.objects.all().order_by('order')
    context = {
        'safety_tips': safety_tips,
    }
    return render(request, 'safety.html', context)

def contact(request):
    if request.method == "GET":
        return render(request, "contact.html")

    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=405)

    try:
        # ✅ READ FORM DATA (NOT JSON)
        name = request.POST.get("name", "").strip()
        email_addr = request.POST.get("email", "").strip()
        mobile = request.POST.get("mobile", "").strip()
        user_type = request.POST.get("userType", "").strip()
        message = request.POST.get("comment", "").strip()

        if not all([name, email_addr, mobile, user_type, message]):
            return JsonResponse(
                {"error": "Please fill all required fields"},
                status=400
            )

        # Save to DB (recommended)
        Contact.objects.create(
            name=name,
            email=email_addr,
            mobile=mobile,
            user_type=user_type,
            comment=message
        )

        # Admin mail
        send_mail(
            subject=f"New Contact Enquiry from {name}",
            message=f"""
            Name: {name}
            Email: {email_addr}
            Mobile: {mobile}
            User Type: {user_type}

            Message:
            {message}
            """,
            from_email="Aorbo Treks <hello@aorbotreks.com>",
            recipient_list=["hello@aorbotreks.com"],
            fail_silently=False,
        )

        # Auto-reply
        ctx = {
            "name": name,
            "current_year": datetime.now().year,
            "cta_url": "https://aorbotreks.com",
            "cta_label": "Visit Our Website",
            "email": email_addr,
        }

        html_content = render_to_string("treks_app/mail.html", ctx)
        text_content = strip_tags(html_content)

        reply = EmailMultiAlternatives(
            subject="Thank you for contacting us!",
            body=text_content,
            from_email="Aorbo Treks <hello@aorbotreks.com>",
            to=[email_addr],
        )
        reply.attach_alternative(html_content, "text/html")
        reply.send()

        return JsonResponse({"message": "Message sent successfully ✅"})

    except Exception as e:
        print("CONTACT ERROR:", e)
        return JsonResponse(
            {"error": "Something went wrong. Please try again later."},
            status=500
        )

def privacy_policy(request):
    return render(request, 'privacypolicy.html')
def terms_and_conditions(request):
    return render(request, 'terms_and_conditions.html')
def user_agreement(request):
    return render(request, 'user_agreement.html')

def index(request):
    whats_new = WhatsNew.objects.all().order_by('-date_posted')[:3]
    top_treks = TopTrek.objects.all()[:4]
    return render(request, 'index.html', {
        'whats_new': whats_new,
        'top_treks': top_treks,
    })

# def search_trek(request):
#     query = request.GET.get("q", "").strip()

#     if not query:
#         return redirect("home")

#     trek = TrekList.objects.filter(
#         Q(name__icontains=query) |
#         Q(state__icontains=query) |
#         Q(tags__name__icontains=query) |
#         Q(trek_points__name__icontains=query)
#     ).distinct().first()

#     if trek:
#         return redirect("card_trek_detail", slug=trek.id)

#     return redirect("home")


# def search_suggestions(request):
#     query = request.GET.get("q", "").strip()

#     if not query:
#         return JsonResponse({"results": []})

#     results = []
#     seen = set()

#     # Match trek name
#     treks = (
#         TrekList.objects
#         .filter(name__istartswith=query)
#         .order_by("name")[:10]
#     )

#     for trek in treks:
#         if trek.id in seen:
#             continue

#         results.append({
#             "label": trek.name,
#             "type": "trek",
#             "trek_name": trek.name,
#             "url": reverse("card_trek_detail", args=[trek.id]),
#         })
#         seen.add(trek.id)

#         if len(results) >= 10:
#             return JsonResponse({"results": results})

#     # 🔹 2. Match trek points (ManyToMany)
#     treks_by_point = (
#         TrekList.objects
#         .filter(trek_points__name__istartswith=query)
#         .distinct()[:10]
#     )

#     for trek in treks_by_point:
#         if trek.id in seen:
#             continue

#         results.append({
#             "label": trek.name,
#             "type": "point",
#             "trek_name": trek.name,
#             "url": reverse("card_trek_detail", args=[trek.id]),
#         })
#         seen.add(trek.id)

#         if len(results) >= 10:
#             break

#     return JsonResponse({"results": results})
def search_trek(request):
    query = request.GET.get("q", "").strip()

    if not query:
        return redirect("home")

    stop_words = [
        "best", "top", "places", "place", "near",
        "visit", "to", "trip", "trips", "treks", "trek"
    ]

    cleaned_query = query.lower()
    for word in stop_words:
        cleaned_query = cleaned_query.replace(word, " ")

    cleaned_query = " ".join(cleaned_query.split())

    # 🔴 SAFETY CHECK
    if not cleaned_query:
        return redirect("home")

    trek = TrekList.objects.filter(
        Q(name__icontains=cleaned_query) |
        Q(state__icontains=cleaned_query) |
        Q(tags__name__icontains=cleaned_query) |
        Q(trek_points__name__icontains=cleaned_query)
    ).distinct().first()

    if trek:
        return redirect("card_trek_detail", trek.id)

    return redirect("home")


from django.http import JsonResponse
from django.urls import reverse
from django.db.models import Q

def search_suggestions(request):
    query = request.GET.get("q", "").strip()

    if not query:
        return JsonResponse({"results": []})

    results = []
    seen = set()

    # ==============================
    # 1️⃣ INTENT SUGGESTIONS (ALWAYS FIRST)
    # ==============================
    intent_templates = [
        f"Best places near {query}",
        f"Top treks near {query}",
        f"Places to visit near {query}",
        f"Weekend trips near {query}",
        f"Adventure treks near {query}",
    ]

    for text in intent_templates:
        results.append({
            "label": text,
            "type": "intent",
            "url": reverse("search_trek") + f"?q={query}"
        })

    # ==============================
    # 2️⃣ TREK NAME MATCH
    # ==============================
    treks = (
        TrekList.objects
        .filter(name__icontains=query)
        .order_by("name")
        .distinct()[:5]
    )

    for trek in treks:
        if trek.id in seen:
            continue

        results.append({
            "label": trek.name,
            "type": "trek",
            "trek_name": trek.name,
            "url": reverse("card_trek_detail", args=[trek.id]),
        })
        seen.add(trek.id)

    # ==============================
    # 3️⃣ TREK POINT / STATE MATCH
    # ==============================
    treks_by_point = (
        TrekList.objects
        .filter(
            Q(trek_points__name__icontains=query) |
            Q(state__icontains=query)
        )
        .distinct()[:5]
    )

    for trek in treks_by_point:
        if trek.id in seen:
            continue

        results.append({
            "label": trek.name,
            "type": "point",
            "trek_name": trek.name,
            "url": reverse("card_trek_detail", args=[trek.id]),
        })
        seen.add(trek.id)

    return JsonResponse({"results": results})


def travel_your_way(request):
    selected_tag = request.GET.get("tag")

    if not selected_tag:
        return redirect('home')

    filtered_treks = [
        t for t in TrekList.objects.all()
        if "tags" in t and selected_tag in t["tags"]
    ]
    context = {
        "selected_tag": selected_tag,
        "treks": filtered_treks,
    }
    return render(request, "travel_your_way.html", context)


def card_trek_detail(request, slug):
    trek = get_object_or_404(TrekList, id=slug)

    activities_list = []
    if trek.activities:
        activities_list = [a.strip() for a in trek.activities.split(",")]

    return render(
        request,
        "card_details.html",
        {
            "trek": trek,
            "TREKS": TrekList.objects.all(),
            "activities_list": activities_list,
        }
    )

