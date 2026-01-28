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
import difflib
import random
    
from .models import (
    Contact, Blog, TrekCategory, TrekOrganizer, Trek, 
    Testimonial, FAQ, SafetyTip, TeamMember, HomepageBanner,
    SocialMedia, ContactInfo, WhatsNew, TopTrek
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


def home(request):
    all_featured_treks = get_featured_treks()

    paginator = Paginator(all_featured_treks, 8)
    page_number = request.GET.get('page', 1)
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


STOP_WORDS = {
    "best", "top", "places", "place", "near",
    "visit", "to", "trip", "trips", "treks", "trek"
}

def normalize(text):
    return text.lower().strip()

def normalize_text(text):
    return text.lower().strip()

def clean_query(query):
    words = normalize(query).split()
    return " ".join(w for w in words if w not in STOP_WORDS)

def score_match(query, text):
    query = normalize(query)
    text = normalize(text)

    score = 0

    if text == query:
        score += 120
    if text.startswith(query):
        score += 100
    if any(word.startswith(query) for word in text.split()):
        score += 80
    if query in text:
        score += 60

    # Typo tolerance (fallback)
    similarity = difflib.SequenceMatcher(None, query, text).ratio()
    if similarity > 0.6:
        score += int(similarity * 40)

    return score

def typo_score(query, text):
    return int(
        difflib.SequenceMatcher(
            None,
            normalize_text(query),
            normalize_text(text)
        ).ratio() * 100
    )


def search_trek(request):
    query = request.GET.get("q", "").strip()
    if not query:
        return redirect("home")

    cleaned_query = clean_query(query)
    if not cleaned_query:
        return redirect("home")

    treks = TrekList.objects.filter(
        Q(name__icontains=cleaned_query) |
        Q(state__icontains=cleaned_query) |
        Q(tags__name__icontains=cleaned_query) |
        Q(trek_points__name__icontains=cleaned_query)
    ).distinct()

    ranked = sorted(
        treks,
        key=lambda t: score_match(cleaned_query, t.name),
        reverse=True
    )

    if ranked:
        return redirect("card_trek_detail", ranked[0].id)

    return redirect("home")


def search_suggestions(request):
    query = request.GET.get("q", "").strip()

    if len(query) < 2:
        return JsonResponse({"results": []})

    query_n = normalize_text(query)
    MAX_RESULTS = 8
    scored = []

    treks = TrekList.objects.all().only("id", "name", "state")

    for trek in treks:
        name = trek.name or ""
        state = trek.state or ""

        score = 0

        # 1️⃣ EXACT PREFIX
        if name.lower().startswith(query_n):
            score += 120

        # 2️⃣ WORD PREFIX
        for word in name.lower().split():
            if word.startswith(query_n):
                score += 90

        # 3️⃣ REAL TYPO TOLERANCE
        score = max(score, typo_score(query_n, name))

        # 4️⃣ STATE MATCH BONUS
        score = max(score, typo_score(query_n, state) - 10)

        if score >= 55:
            scored.append((score, trek))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    seen = set()

    for score, trek in scored[:MAX_RESULTS]:
        if trek.id in seen:
            continue

        results.append({
            "label": trek.name,
            "type": "trek",
            "url": reverse("card_trek_detail", args=[trek.id]),
        })
        seen.add(trek.id)

    if results:
        results.append({
            "label": f"Best treks near {query}",
            "type": "intent",
            "url": reverse("search_trek") + f"?q={query}",
        })

    return JsonResponse({"results": results})


def about(request):
    return render(request, 'about.html', {
        'team_members': TeamMember.objects.all().order_by('order')
    })

def blogs(request):
    paginator = Paginator(Blog.objects.order_by('-created_at'), 6)
    return render(request, 'blogs.html', {
        'blogs': paginator.get_page(request.GET.get('page'))
    })

def blog_detail(request, slug):
    blog = get_object_or_404(Blog, slug=slug)
    return render(request, 'blog_detail.html', {
        'blog': blog,
        'recent_blogs': Blog.objects.exclude(id=blog.id)[:3]
    })

def treks(request):
    category_id = request.GET.get('category')
    difficulty = request.GET.get('difficulty')

    all_treks = Trek.objects.all()
    if category_id:
        all_treks = all_treks.filter(category_id=category_id)
    if difficulty:
        all_treks = all_treks.filter(difficulty=difficulty)

    paginator = Paginator(all_treks, 12)

    return render(request, 'treks.html', {
        'treks': paginator.get_page(request.GET.get('page')),
        'categories': TrekCategory.objects.all(),
        'selected_category': category_id,
        'selected_difficulty': difficulty,
        'difficulty_choices': Trek.DIFFICULTY_CHOICES,
    })

def trek_detail(request, slug):
    trek = get_object_or_404(Trek, slug=slug)
    return render(request, 'trek_detail.html', {
        'trek': trek,
        'testimonials': trek.testimonials.all(),
        'similar_treks': Trek.objects.filter(category=trek.category).exclude(id=trek.id)[:3],
    })

def safety(request):
    return render(request, 'safety.html', {
        'safety_tips': SafetyTip.objects.all().order_by('order')
    })

def detect_trek_category(message: str):
    message = message.lower()

    if any(word in message for word in ["adventure", "hills", "mountain", "climb"]):
        return "adventure"

    if any(word in message for word in ["camp", "camping", "tent", "bonfire"]):
        return "camping"

    if any(word in message for word in ["nature", "green", "greenery", "forest", "waterfall"]):
        return "nature"

    if any(word in message for word in ["beach", "sea", "coast"]):
        return "beach"

    if any(word in message for word in ["spiritual", "temple", "holy", "pilgrimage"]):
        return "spiritual"

    if any(word in message for word in ["weekend", "short trip", "getaway"]):
        return "weekend"

    return None



def contact(request):

    if request.method == "GET":
        return render(request, "contact.html")

    # -------------------------
    # FORM DATA
    # -------------------------
    name = request.POST.get("name")
    email = request.POST.get("email")
    mobile = request.POST.get("mobile")
    user_type = request.POST.get("user_type")   # trekker / organizer / other
    message = request.POST.get("comment")
    trek_category = request.POST.get("trek_category")  # Category selected in dropdown

    # Validate all required fields
    if not all([name, email, mobile, user_type, message]):
        return JsonResponse({"error": "Please fill all required fields"}, status=400)

    # Save to database
    Contact.objects.create(
        name=name, email=email, mobile=mobile,
        user_type=user_type, comment=message
    )

    # -------------------------
    # TREK LINKS
    # -------------------------
    TREK_LINKS = {
        "adventure": "https://www.aorbotreks.com/travel-your-way/?tag=adventure",
        "camping": "https://www.aorbotreks.com/travel-your-way/?tag=camping",
        "nature": "https://www.aorbotreks.com/travel-your-way/?tag=nature",
        "beach": "https://www.aorbotreks.com/travel-your-way/?tag=beach",
        "spiritual": "https://www.aorbotreks.com/travel-your-way/?tag=spiritual",
        "weekend": "https://www.aorbotreks.com/travel-your-way/?tag=weekend",
    }

    # -------------------------
    # LOGIC PER USER TYPE
    # -------------------------
    detected_category = None
    explore_link = "https://www.aorbotreks.com"
    subject = "We've Received Your Query – Aorbo Treks"
    template_name = "emails/contact_default.html"

    if user_type == "trekker":
        if trek_category:
            detected_category = trek_category
        else:
            detected_category = detect_trek_category(message)
        
        explore_link = TREK_LINKS.get(
            detected_category,
            "https://www.aorbotreks.com/treks"
        )
        subject = f"{detected_category.title() if detected_category else 'Explore'} Treks – Aorbo Treks"
        template_name = "emails/trekker.html"

    elif user_type == "organizer":
        explore_link = "https://partner.aorbotreks.com"
        subject = "Partnership Request – Aorbo Treks"
        template_name = "emails/organizer.html"

    else:
        explore_link = "https://www.aorbotreks.com"
        subject = "We've Received Your Query – Aorbo Treks"
        template_name = "emails/other.html"

    display_category = detected_category.title() if detected_category else "Our Featured"
    
    context = {
        "name": name,
        "email": email,
        "message": message,
        "detected_category": detected_category,
        "display_category": display_category,
        "explore_link": explore_link,
        "current_year": datetime.now().year,
    }

    html_content = render_to_string(template_name, context)

    try:
        mail = EmailMultiAlternatives(
            subject=subject,
            body="Thank you for contacting Aorbo Treks.",
            from_email="Aorbo Treks <" + settings.DEFAULT_FROM_EMAIL + ">",
            to=[email],
        )
        mail.attach_alternative(html_content, "text/html")
        mail.send()
    except Exception as e:
        return JsonResponse({"error": f"Failed to send email: {str(e)}"}, status=500)

    return JsonResponse({"message": "Message sent successfully"})

def travel_your_way(request):
    selected_tag = request.GET.get("tag")
    if not selected_tag:
        return redirect("home")

    treks = TrekList.objects.filter(tags__name__iexact=selected_tag).distinct()
    return render(request, "travel_your_way.html", {
        "selected_tag": selected_tag,
        "treks": treks,
    })



def card_trek_detail(request, slug):
    trek = get_object_or_404(TrekList, id=slug)

    related_treks = (
        trek.related_treks.all()
        if hasattr(trek, "related_treks")
        else TrekList.objects.none()
    )

    activities_list = []
    if trek.activities:
        activities_list = [a.strip() for a in trek.activities.split(",")]

    return render(
        request,
        "card_details.html",
        {
            "trek": trek,
            "related_treks": related_treks,   
            "activities_list": activities_list,
        }
    )

def privacy_policy(request):
    return render(request, "privacypolicy.html")


def terms_and_conditions(request):
    return render(request, "terms_and_conditions.html")


def user_agreement(request):
    return render(request, "user_agreement.html")

