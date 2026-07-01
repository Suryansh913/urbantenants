import json
import re
import logging

import google.generativeai as genai
import google.api_core.exceptions
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings

from listings.models import listings

logger = logging.getLogger(__name__)

# =====================================================
# GEMINI SETUP
# =====================================================

genai.configure(api_key=settings.GEMINI_API_KEY)

MODEL_NAMES = [
    "gemini-2.0-flash",
    "gemini-flash-lite-latest",
    "gemini-2.5-flash",
]
_MODEL_CACHE = {}


def get_model(name):
    if name not in _MODEL_CACHE:
        _MODEL_CACHE[name] = genai.GenerativeModel(name)
    return _MODEL_CACHE[name]


SYSTEM_PROMPT = """
You are Cribmate Bot, the AI assistant for UrbanTenants — a room renting platform.

Your job:
1. Help users find rooms.
2. Explain the booking process.
3. Explain documents required.
4. Explain rent and security deposit.
5. Answer all UrbanTenants-related questions.
6. Answer questions about UrbanTenants itself (founder, contact, support).

ABOUT US:
- Founder: Suryansh Shukla
- Suryansh Shukla is the founder of UrbanTenants. He is a technology
  enthusiast and entrepreneur focused on solving real-world housing and
  rental challenges through technology.

CONTACT & SUPPORT:
- Email: suryansh@urbantenants.com
- Phone: 8303970186
- For any booking, payment, or account issues, direct users to this email
  or phone number.

When a user asks about the founder, "who made this", "who owns
UrbanTenants", contact details, or how to reach support, answer using the
ABOUT US / CONTACT & SUPPORT details above. Always use the "reply" action
shape for these questions (not "search_room").

LANGUAGE RULES (very important):
- Detect the language/style the user is writing in and ALWAYS reply in that
  same language and script.
- If the user writes in English -> reply in English, and set "lang" to "en".
- If the user writes in Hindi using Devanagari script (e.g. "मुझे कमरा चाहिए")
  -> reply in Hindi using Devanagari script, and set "lang" to "hi".
- If the user writes Hindi in Roman/English letters (Hinglish, e.g. "mujhe
  kamra chahiye", "rent kitna hai") -> reply in Hinglish using Roman script
  (NOT Devanagari), and set "lang" to "hinglish".
- Never mix scripts within a single reply.

PAGE NAVIGATION RULES (very important):
- If the user asks to go to / open / visit / navigate to a specific page,
  return the "navigate" action with the correct "url_name" from this list:

  PAGE NAME          | url_name
  -------------------|----------------
  home / main        | base
  2bhk               | bhk2
  3bhk               | bhk3
  pg                 | pg
  about us           | aboutus
  terms & conditions | Terms-condition
  privacy policy     | privacy-policy
  booking / book     | bookingform   <- special: tell user to pick a room first
  invoice            | invoice       <- special: tell user to log in & visit My Bookings

- For "bookingform" and "invoice" pages, do NOT navigate directly.
  Instead return action "reply" and guide the user as described below.

- For bookingform: tell the user to first browse rooms, open the room they
  like, and click the "Book Now" button on that room's page.
- For invoice: tell the user to log in to their account and go to
  "My Bookings" to view their invoice. Do NOT give a direct URL.

OUTPUT FORMAT (very important):
You must respond with ONLY raw JSON — no markdown code fences, no commentary,
no text before or after the JSON object. Pick exactly one of the three shapes
below.

If the user is searching for a room, return:
{
  "action": "search_room",
  "lang": "en" | "hi" | "hinglish",
  "location": "",
  "room_type": "",
  "wifi": false,
  "ac": false,
  "bed": false,
  "table": false,
  "chair": false,
  "fan": false,
  "ro": false,
  "mattress": false
}

If the user wants to navigate to a page, return:
{
  "action": "navigate",
  "lang": "en" | "hi" | "hinglish",
  "url_name": "<one of the url_names from the table above>",
  "message": "short confirmation message in the user's language"
}

If the user is asking a question or making general conversation, return:
{
  "action": "reply",
  "lang": "en" | "hi" | "hinglish",
  "message": "your answer here, written in the same language/script as the user"
}

Examples:

User: Need 2bhk in nawabganj with wifi
Output:
{"action":"search_room","lang":"en","location":"nawabganj","room_type":"2bhk","wifi":true,"ac":false,"bed":false,"table":false,"chair":false,"fan":false,"ro":false,"mattress":false}

User: mujhe lucknow me pg chahiye
Output:
{"action":"search_room","lang":"hinglish","location":"lucknow","room_type":"","wifi":false,"ac":false,"bed":false,"table":false,"chair":false,"fan":false,"ro":false,"mattress":false}

User: rent kitna hota hai
Output:
{"action":"reply","lang":"hinglish","message":"Rent property aur location ke hisab se alag hota hai. Aap city batao, main best options dikhata hoon."}

User: मुझे डिपॉजिट के बारे में बताओ
Output:
{"action":"reply","lang":"hi","message":"सिक्योरिटी डिपॉजिट आमतौर पर 1-2 महीने के किराए के बराबर होता है और यह रिफंडेबल होता है।"}

User: Who is the founder of UrbanTenants?
Output:
{"action":"reply","lang":"en","message":"UrbanTenants was founded by Suryansh Shukla, a technology enthusiast and entrepreneur focused on solving real-world housing and rental challenges through technology."}

User: support se kaise contact kare
Output:
{"action":"reply","lang":"hinglish","message":"Aap support se is tarah contact kar sakte hai: Email - suryansh@urbantenants.com, Phone - 8303970186."}

User: take me to about us page
Output:
{"action":"navigate","lang":"en","url_name":"aboutus","message":"Taking you to the About Us page!"}

User: mujhe home page pe le chalo
Output:
{"action":"navigate","lang":"hinglish","url_name":"base","message":"Aapko home page pe le ja raha hoon!"}

User: मुझे 2BHK पेज पर ले जाओ
Output:
{"action":"navigate","lang":"hi","url_name":"bhk2","message":"आपको 2BHK पेज पर ले जा रहा हूँ!"}

User: booking karna hai
Output:
{"action":"reply","lang":"hinglish","message":"Booking ke liye pehle koi room browse karo, phir us room ko open karo aur 'Book Now' button click karo. Main aapke liye rooms dhundh sakta hoon — location batao!"}

User: mujhe invoice dekhna hai
Output:
{"action":"reply","lang":"hinglish","message":"Invoice dekhne ke liye apne account mein login karo aur 'My Bookings' section mein jao. Wahan aapko apni booking ka invoice milega."}

User: show me pg page
Output:
{"action":"navigate","lang":"en","url_name":"pg","message":"Taking you to the PG listings page!"}
"""

# =====================================================
# CONSTANTS
# =====================================================

# Only these url_names can be navigated to directly.
# bookingform and invoice are intentionally excluded — handled via "reply".
NAVIGATE_ALLOWED_PAGES = {
    "base",
    "bhk2",
    "bhk3",
    "pg",
    "aboutus",
    "Terms-condition",
    "privacy-policy",
}

AMENITY_FIELD_MAP = {
    "wifi": "wifi",
    "ac": "Ac",
    "bed": "bed",
    "table": "table",
    "chair": "chair",
    "fan": "fan",
    "ro": "ro",
    "mattress": "mattres",
}

VALID_LANGS = {"en", "hi", "hinglish"}

FALLBACK_MESSAGES = {
    "en": "Sorry, I'm having trouble understanding that right now. Could you try rephrasing, or ask about booking, rent, documents, or rooms?",
    "hi": "माफ़ कीजिए, अभी मुझे समझने में दिक्कत हो रही है। कृपया दोबारा पूछें, या बुकिंग, किराया, दस्तावेज़ों, या कमरों के बारे में पूछें।",
    "hinglish": "Maaf kijiye, abhi samajhne mein dikkat ho rahi hai. Dobara try kare, ya booking, rent, documents, ya rooms ke baare mein puche.",
}

QUOTA_EXCEEDED_MESSAGES = {
    "en": "Our AI assistant has reached its usage limit for today. Please try again in a little while, or contact support directly.",
    "hi": "हमारे AI सहायक की आज की उपयोग सीमा समाप्त हो गई है। कृपया थोड़ी देर बाद फिर से प्रयास करें, या सीधे सपोर्ट से संपर्क करें।",
    "hinglish": "Hamare AI assistant ki aaj ki usage limit khatam ho gayi hai. Thodi der baad phir try kare, ya directly support se contact kare.",
}

NO_ROOMS_MESSAGES = {
    "en": "No rooms found matching that criteria. Try adjusting the location or amenities.",
    "hi": "इस मापदंड से मेल खाता कोई कमरा नहीं मिला। लोकेशन या सुविधाएं बदलकर देखें।",
    "hinglish": "Is criteria se match karta koi room nahi mila. Location ya amenities adjust karke try kare.",
}


# =====================================================
# HELPERS
# =====================================================

def normalize_lang(lang):
    return lang if lang in VALID_LANGS else "en"


DEVANAGARI_RANGE = re.compile(r'[\u0900-\u097F]')

HINGLISH_MARKERS = [
    "kya", "hai", "kaise", "kitna", "kitne", "chahiye", "karna",
    "karo", "kare", "hota", "milega", "mujhe", "aap", "apna",
    "khali", "wala", "bhi", "nahi", "haan", "paise", "ghar",
    "kab", "kahan", "konsa", "konsi", "lagenge", "lagega", "booking",
]


def guess_lang_heuristic(text):
    """
    A quick local (non-LLM) language guess used ONLY as a fallback when
    Gemini itself fails to respond at all — so that even the error message
    comes back in roughly the right language instead of always defaulting
    to English regardless of what the user actually wrote.
    """
    if DEVANAGARI_RANGE.search(text):
        return "hi"
    words = text.lower().split()
    if any(w in HINGLISH_MARKERS for w in words):
        return "hinglish"
    return "en"


def extract_json_from_gemini(raw_text):
    """
    Gemini is instructed to return raw JSON only, but LLMs sometimes still
    wrap it in markdown fences or add stray text around it. This strips
    common wrapping and finds the first {...} block as a best-effort
    safety net, so a slightly-off response doesn't crash the whole request.
    """
    text = raw_text.strip()

    # Strip markdown code fences if present
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Fallback: find the first balanced-looking {...} block in the text
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return None


LANG_DISPLAY_NAMES = {
    "en": "English",
    "hi": "Hindi (Devanagari script)",
    "hinglish": "Hinglish (Hindi written in Roman/English letters, NOT Devanagari)",
}


def call_gemini_safely(user_message, detected_lang, retries=1):
    """
    Calls Gemini and returns (raw_text, error_reason, is_quota_error).

    Tries each model in MODEL_NAMES in order. If a model returns a 429
    ResourceExhausted (quota exhausted), we move to the next model.
    is_quota_error is only True if EVERY model in the list is exhausted.
    """
    lang_name = LANG_DISPLAY_NAMES.get(detected_lang, "English")
    prompt = (
        SYSTEM_PROMPT
        + f"\n\nIMPORTANT: This specific message has been detected as: {lang_name}. "
        + f"You MUST write your reply in {lang_name}, and set \"lang\" to \"{detected_lang}\" "
        + "in your JSON output, regardless of what language earlier messages in this "
        + "conversation may have been in. Always follow the CURRENT message's language.\n\n"
        + "User: " + user_message
    )

    last_error = None
    all_quota_exhausted = True

    for model_name in MODEL_NAMES:
        model = get_model(model_name)
        model_exhausted = False

        for attempt in range(retries + 1):
            try:
                response = model.generate_content(prompt)
            except google.api_core.exceptions.ResourceExhausted as e:
                last_error = f"[{model_name}] 429 ResourceExhausted (quota/rate limit): {e!r}"
                logger.warning(
                    "[Gemini attempt %d, model=%s] QUOTA EXCEEDED, trying next model: %s",
                    attempt + 1, model_name, last_error,
                )
                model_exhausted = True
                break
            except Exception as e:
                last_error = f"[{model_name}] generate_content raised: {e!r}"
                logger.warning("[Gemini attempt %d, model=%s] %s", attempt + 1, model_name, last_error)
                continue

            candidates = getattr(response, "candidates", None)
            if not candidates:
                prompt_feedback = getattr(response, "prompt_feedback", None)
                last_error = f"[{model_name}] No candidates returned. prompt_feedback={prompt_feedback!r}"
                logger.warning("[Gemini attempt %d, model=%s] %s", attempt + 1, model_name, last_error)
                continue

            finish_reason = getattr(candidates[0], "finish_reason", None)
            try:
                raw_text = response.text or ""
            except Exception as e:
                safety_ratings = getattr(candidates[0], "safety_ratings", None)
                last_error = (
                    f"[{model_name}] response.text access raised: {e!r} | "
                    f"finish_reason={finish_reason!r} | safety_ratings={safety_ratings!r}"
                )
                logger.warning("[Gemini attempt %d, model=%s] %s", attempt + 1, model_name, last_error)
                continue

            if not raw_text.strip():
                last_error = f"[{model_name}] Empty text in response. finish_reason={finish_reason!r}"
                logger.warning("[Gemini attempt %d, model=%s] %s", attempt + 1, model_name, last_error)
                continue

            if model_name != MODEL_NAMES[0]:
                logger.info("[Gemini] Fell back to model '%s' successfully.", model_name)
            return raw_text, None, False

        if not model_exhausted:
            all_quota_exhausted = False

    return "", last_error, all_quota_exhausted


def search_rooms_from_gemini_result(result):
    """Applies the filters Gemini extracted to the listings queryset."""
    from django.db.models import Q

    rooms = listings.objects.filter(Room_available=True)

    location = (result.get("location") or "").strip()
    if location:
        rooms = rooms.filter(
            Q(location_name__icontains=location) | Q(Room_title__icontains=location)
        )

    room_type = (result.get("room_type") or "").strip()
    if room_type:
        rooms = rooms.filter(Room_type__icontains=room_type)

    for gemini_key, field_name in AMENITY_FIELD_MAP.items():
        if result.get(gemini_key):
            rooms = rooms.filter(**{field_name: True})

    return rooms[:10]


def serialize_rooms(rooms):
    room_data = []
    for room in rooms:
        amenities = []
        if room.wifi:
            amenities.append("WiFi")
        if room.Ac:
            amenities.append("AC")
        if room.bed:
            amenities.append("Bed")
        if room.table:
            amenities.append("Table")
        if room.chair:
            amenities.append("Chair")
        if room.fan:
            amenities.append("Fan")
        if room.ro:
            amenities.append("RO Water")
        if room.mattres:
            amenities.append("Mattress")

        image_url = ""
        if room.Room_images1:
            try:
                image_url = str(room.Room_images1.url)
            except Exception:
                image_url = ""

        room_data.append({
            "id": room.id,
            "title": room.Room_title,
            "rent": room.Room_rent,
            "location": room.location_name or room.Room_title or "Location not specified",
            "image": image_url,
            "amenities": amenities,
        })
    return room_data


# =====================================================
# VIEWS
# =====================================================

def chat_page(request):
    return render(request, "chatbot.html")


def chat_api(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            "reply": FALLBACK_MESSAGES["en"],
            "lang": "en",
        }, status=400)

    user_message = (data.get("message") or "").strip()

    if not user_message:
        return JsonResponse({
            "reply": FALLBACK_MESSAGES["en"],
            "lang": "en",
        }, status=400)

    # Used ONLY if Gemini fails completely, so the error message itself
    # still comes back in roughly the right language.
    heuristic_lang = guess_lang_heuristic(user_message)

    # ---- Call Gemini (with detailed failure logging + 1 retry) ----
    raw_text, error_reason, is_quota_error = call_gemini_safely(user_message, heuristic_lang, retries=1)

    if error_reason is not None:
        logger.error(
            "Gemini call failed for message=%r. Reason: %s",
            user_message, error_reason,
        )
        if is_quota_error:
            return JsonResponse({
                "reply": QUOTA_EXCEEDED_MESSAGES[heuristic_lang],
                "lang": heuristic_lang,
            })
        return JsonResponse({
            "reply": FALLBACK_MESSAGES[heuristic_lang],
            "lang": heuristic_lang,
        })

    result = extract_json_from_gemini(raw_text)

    if result is None:
        logger.warning(
            "Could not parse Gemini JSON for message=%r. Raw response: %r",
            user_message, raw_text,
        )
        plain_text = raw_text.strip()
        if plain_text:
            return JsonResponse({"reply": plain_text, "lang": heuristic_lang})
        return JsonResponse({
            "reply": FALLBACK_MESSAGES[heuristic_lang],
            "lang": heuristic_lang,
        })

    # Trust our own deterministic per-message detection over whatever
    # Gemini echoed back in "lang".
    lang = heuristic_lang
    action = result.get("action")

    # =========================
    # NAVIGATION
    # =========================
    if action == "navigate":
        url_name = (result.get("url_name") or "").strip()
        nav_message = result.get("message") or ""

        # Safety whitelist — bookingform & invoice are never allowed here
        if url_name not in NAVIGATE_ALLOWED_PAGES:
            # Gemini tried to navigate to a restricted/unknown page.
            # Fall back to a plain reply so we never expose raw URLs.
            return JsonResponse({
                "reply": nav_message or FALLBACK_MESSAGES[lang],
                "lang": lang,
            })

        try:
            from django.urls import reverse
            url = reverse(url_name)
        except Exception:
            logger.warning("navigate: reverse() failed for url_name=%r", url_name)
            return JsonResponse({
                "reply": nav_message or FALLBACK_MESSAGES[lang],
                "lang": lang,
            })

        return JsonResponse({
            "type": "navigate",
            "url": url,
            "message": nav_message,
            "lang": lang,
        })

    # =========================
    # ROOM SEARCH
    # =========================
    if action == "search_room":
        rooms = search_rooms_from_gemini_result(result)

        if rooms.exists():
            return JsonResponse({
                "type": "listing",
                "rooms": serialize_rooms(rooms),
                "lang": lang,
            })

        return JsonResponse({
            "reply": NO_ROOMS_MESSAGES[lang],
            "lang": lang,
        })

    # =========================
    # NORMAL CHAT
    # =========================
    message = result.get("message") or FALLBACK_MESSAGES[lang]
    return JsonResponse({
        "reply": message,
        "lang": lang,
    })