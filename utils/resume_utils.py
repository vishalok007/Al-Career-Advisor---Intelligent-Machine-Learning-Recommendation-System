import pdfplumber
import re


def extract_text_from_pdf(uploaded_file):
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def extract_skills_from_text(text, skill_list):
    text = text.lower()
    found_skills = []
    for skill in skill_list:
        if skill.lower() in text:
            found_skills.append(skill)
    return found_skills

_LOCATION_KEYWORDS = [
    "Bangalore", "Bengaluru", "Hyderabad", "Chennai", "Mumbai", "Pune",
    "Delhi", "Gurgaon", "Gurugram", "Noida", "Kolkata", "Ahmedabad",
    "Jaipur", "Indore", "Kochi", "Coimbatore", "Trivandrum",
    "New York", "San Francisco", "Seattle", "Austin", "Boston", "Chicago",
    "Los Angeles", "San Diego", "Atlanta", "Dallas", "Denver", "Toronto",
    "Vancouver", "London", "Manchester", "Dublin", "Berlin", "Munich",
    "Amsterdam", "Paris", "Singapore", "Tokyo", "Sydney", "Melbourne",
    "Dubai", "Remote",
]

_LOCATION_COUNTRY_HINTS = {
    "India": ["Bangalore", "Bengaluru", "Hyderabad", "Chennai", "Mumbai", "Pune",
              "Delhi", "Gurgaon", "Gurugram", "Noida", "Kolkata", "India"],
    "USA": ["United States", "USA", "New York", "San Francisco", "Seattle",
            "Austin", "Boston", "Chicago", "Los Angeles", "San Diego",
            "Atlanta", "Dallas", "Denver"],
    "UK": ["London", "Manchester", "United Kingdom", "UK"],
    "Canada": ["Toronto", "Vancouver", "Canada"],
    "Europe": ["Berlin", "Munich", "Amsterdam", "Paris", "Dublin"],
    "APAC": ["Singapore", "Tokyo", "Sydney", "Melbourne"],
    "UAE": ["Dubai", "UAE"],
}


def extract_location_from_text(text):
    """Best-effort detection of candidate's most-likely work location."""
    if not text:
        return None
    for token in sorted(_LOCATION_KEYWORDS, key=len, reverse=True):
        if re.search(rf"\b{re.escape(token)}\b", text, flags=re.IGNORECASE):
            return token
    return None


def location_country_hint(city_or_country):
    """Return a coarse country/region label from a city string."""
    if not city_or_country:
        return ""
    for region, tokens in _LOCATION_COUNTRY_HINTS.items():
        for t in tokens:
            if t.lower() in city_or_country.lower():
                return region
    return ""


def extract_role_mentions(text, roles):
    """Return job roles that the resume explicitly mentions as titles."""
    if not text or not roles:
        return []
    out = []
    low = text.lower()
    for role in roles:
        if role.lower() in low:
            out.append(role)
    return out
