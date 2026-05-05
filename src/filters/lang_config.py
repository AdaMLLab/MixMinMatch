"""
Language-specific configurations for quality filters.

This module contains Unicode ranges, punctuation, policy phrases, and
repetition patterns for each supported language.
"""
import re


# =============================================================================
# Arabic Configuration
# =============================================================================
ARABIC_SCRIPT_RANGE = re.compile(
    r'[\u0600-\u06FF'    # Arabic
    r'\u0750-\u077F'     # Arabic Supplement
    r'\u08A0-\u08FF'     # Arabic Extended-A
    r'\uFB50-\uFDFF'     # Arabic Presentation Forms-A
    r'\uFE70-\uFEFF]'    # Arabic Presentation Forms-B
)

ARABIC_TERMINAL_PUNCTUATION = (
    # Latin punctuation (commonly used in modern Arabic web text)
    '.', '!', '?', '"', "'",
    # Arabic-specific punctuation
    '\u061F',  # ؟ Arabic question mark
    '\u06D4',  # ۔ Arabic full stop
    '\u061E',  # ؞ Arabic triple dot punctuation mark
    '\u061D',  # ؝ Arabic end of text mark
    # Common line-ending characters
    ':', ';', ')', ']',
    '\u00BB',  # » Right-pointing double angle quotation mark
    '\u201D',  # " Right double quotation mark
    '\u2019',  # ' Right single quotation mark
    '\u300B',  # 》 Right double angle bracket
)

ARABIC_POLICY_PHRASES = [
    "سياسة الخصوصية",           # privacy policy
    "شروط الاستخدام",           # terms of use
    "شروط الخدمة",              # terms of service
    "سياسة ملفات تعريف الارتباط",  # cookie policy
    "ملفات تعريف الارتباط",      # cookies
    "نستخدم ملفات تعريف الارتباط",  # we use cookies
    "جميع الحقوق محفوظة",        # all rights reserved
    "حقوق الطبع والنشر",         # copyright
    "حقوق النشر محفوظة",         # copyright reserved
    "اشترك في النشرة الإخبارية",  # subscribe to newsletter
    "سجل في النشرة",            # sign up for newsletter
    "للاشتراك في القائمة البريدية",  # to subscribe to mailing list
    "أدخل بريدك الإلكتروني",     # enter your email
    "تسجيل الدخول",             # login
    "إنشاء حساب",               # create account
    "هل نسيت كلمة المرور",       # forgot password
    "تابعنا على",               # follow us on
    "شاركنا على",               # share on
    "اقرأ المزيد",              # read more
    "المزيد من المقالات",        # more articles
    "مقالات ذات صلة",           # related articles
    "التعليقات مغلقة",          # comments closed
    "اترك تعليقا",              # leave a comment
]

ARABIC_PLACEHOLDER_PATTERNS = [
    "هذا النص هو مثال",          # this text is an example
    "نص تجريبي",                # test text
    "هذا نص وهمي",              # this is dummy text
]

ARABIC_CITATION_REGEX = re.compile(
    r'\[\d+\]|\[edit\]|\[citation needed\]|\[بحاجة لمصدر\]|\[تحرير\]'
)

ARABIC_REPETITION_PATTERNS = re.compile(
    r'[هخ]{4,}|'       # هههه or خخخخ (laughter)
    r'[اآ]{4,}|'        # آآآآ (exclamation)
    r'[و]{4,}|'         # وووو (exclamation)
    r'[ي]{4,}'          # يييي (exclamation)
)


# =============================================================================
# Turkish Configuration
# =============================================================================
# Turkish uses Latin script with additional characters
# We detect Turkish by looking for Turkish-specific Latin characters
TURKISH_SCRIPT_RANGE = re.compile(
    r'[a-zA-Z'          # Basic Latin
    r'ğĞ'               # g with breve
    r'ıİ'               # dotless i / dotted I
    r'öÖ'               # o with umlaut
    r'üÜ'               # u with umlaut
    r'şŞ'               # s with cedilla
    r'çÇ]'              # c with cedilla
)

# Turkish-specific characters (for language detection)
TURKISH_SPECIFIC_CHARS = re.compile(r'[ğĞıİşŞçÇöÖüÜ]')

TURKISH_TERMINAL_PUNCTUATION = (
    # Standard Latin punctuation
    '.', '!', '?', '"', "'",
    ':', ';', ')', ']',
    '\u00BB',  # »
    '\u201D',  # "
    '\u2019',  # '
)

TURKISH_POLICY_PHRASES = [
    "gizlilik politikası",      # privacy policy
    "gizlilik sözleşmesi",      # privacy agreement
    "kullanım şartları",        # terms of use
    "kullanım koşulları",       # terms of conditions
    "hizmet şartları",          # terms of service
    "çerez politikası",         # cookie policy
    "çerezleri kullanıyoruz",   # we use cookies
    "çerez kullanımı",          # cookie usage
    "tüm hakları saklıdır",     # all rights reserved
    "telif hakkı",              # copyright
    "bültene abone ol",         # subscribe to newsletter
    "e-bülten",                 # e-newsletter
    "e-posta adresinizi girin", # enter your email
    "giriş yap",                # login
    "oturum aç",                # sign in
    "hesap oluştur",            # create account
    "kayıt ol",                 # register
    "şifremi unuttum",          # forgot password
    "bizi takip edin",          # follow us
    "sosyal medya",             # social media
    "ilgili yazılar",           # related articles
    "ilgili haberler",          # related news
    "devamını oku",             # read more
    "daha fazla",               # more
    "yorum yap",                # leave a comment
    "yorumlar kapalı",          # comments closed
]

TURKISH_PLACEHOLDER_PATTERNS = [
    "bu bir örnek metindir",    # this is an example text
    "deneme metni",             # test text
    "örnek metin",              # sample text
]

TURKISH_CITATION_REGEX = re.compile(
    r'\[\d+\]|\[edit\]|\[citation needed\]|\[düzenle\]|\[kaynak belirtilmeli\]'
)

# Turkish laughter and expression patterns
TURKISH_REPETITION_PATTERNS = re.compile(
    r'[js]{4,}|'        # jsjsjsjs (Turkish laughter)
    r'[kd]{4,}|'        # kdkdkdkd (Turkish laughter)
    r'[ah]{4,}|'        # ahahahah (laughter)
    r'[ha]{4,}|'        # hahahaha (laughter)
    r'[sj]{4,}'         # sjsjsjsj (laughter variant)
)


# =============================================================================
# Hindi Configuration
# =============================================================================
HINDI_SCRIPT_RANGE = re.compile(
    r'[\u0900-\u097F'    # Devanagari
    r'\uA8E0-\uA8FF'     # Devanagari Extended
    r'\u1CD0-\u1CFF]'    # Vedic Extensions
)

HINDI_TERMINAL_PUNCTUATION = (
    # Devanagari punctuation
    '\u0964',  # । Devanagari Danda
    '\u0965',  # ॥ Devanagari Double Danda
    # Latin punctuation (used in modern Hindi web text)
    '.', '!', '?', '"', "'",
    ':', ';', ')', ']',
    '\u00BB',  # »
    '\u201D',  # "
    '\u2019',  # '
)

HINDI_POLICY_PHRASES = [
    "गोपनीयता नीति",            # privacy policy
    "निजता नीति",              # privacy policy (alternate)
    "सेवा की शर्तें",           # terms of service
    "उपयोग की शर्तें",          # terms of use
    "नियम और शर्तें",           # terms and conditions
    "कुकी नीति",               # cookie policy
    "कुकीज़ का उपयोग",          # use of cookies
    "सभी अधिकार सुरक्षित",       # all rights reserved
    "कॉपीराइट",                # copyright
    "न्यूज़लेटर",               # newsletter
    "न्यूज़लेटर सदस्यता",        # newsletter subscription
    "ईमेल दर्ज करें",           # enter email
    "अपना ईमेल दर्ज करें",       # enter your email
    "लॉगिन करें",              # login
    "साइन इन",                 # sign in
    "खाता बनाएं",              # create account
    "रजिस्टर करें",             # register
    "पासवर्ड भूल गए",           # forgot password
    "हमें फॉलो करें",           # follow us
    "सोशल मीडिया",             # social media
    "संबंधित लेख",             # related articles
    "संबंधित समाचार",           # related news
    "और पढ़ें",                # read more
    "अधिक जानें",              # learn more
    "टिप्पणी करें",             # leave a comment
    "टिप्पणियाँ बंद",           # comments closed
]

HINDI_PLACEHOLDER_PATTERNS = [
    "यह एक उदाहरण है",          # this is an example
    "परीक्षण पाठ",              # test text
    "नमूना पाठ",               # sample text
    "डमी टेक्स्ट",              # dummy text
]

HINDI_CITATION_REGEX = re.compile(
    r'\[\d+\]|\[edit\]|\[citation needed\]|\[संपादित करें\]|\[उद्धरण आवश्यक\]'
)

# Hindi laughter and expression patterns
HINDI_REPETITION_PATTERNS = re.compile(
    r'[ह]{4,}|'         # हहहह (laughter)
    r'[अ]{4,}|'         # अअअअ (exclamation)
    r'[आ]{4,}|'         # आआआआ (exclamation)
    r'[ओ]{4,}|'         # ओओओओ (exclamation)
    r'[ए]{4,}'          # एएएए (exclamation)
)


# =============================================================================
# Italian Configuration
# =============================================================================
# Italian uses Latin script with accented vowels
ITALIAN_SCRIPT_RANGE = re.compile(
    r'[a-zA-Z'          # Basic Latin
    r'àÀ'               # a with grave
    r'èÈ'               # e with grave
    r'éÉ'               # e with acute
    r'ìÌ'               # i with grave
    r'òÒ'               # o with grave
    r'ùÙ]'              # u with grave
)

# Italian-specific characters (accented vowels for language detection)
ITALIAN_SPECIFIC_CHARS = re.compile(r'[àÀèÈéÉìÌòÒùÙ]')

ITALIAN_TERMINAL_PUNCTUATION = (
    # Standard Latin punctuation
    '.', '!', '?', '"', "'",
    ':', ';', ')', ']',
    '\u00BB',  # »
    '\u201D',  # "
    '\u2019',  # '
)

ITALIAN_POLICY_PHRASES = [
    "informativa sulla privacy",    # privacy policy
    "politica sulla privacy",       # privacy policy (alternate)
    "termini di servizio",          # terms of service
    "termini di utilizzo",          # terms of use
    "condizioni d'uso",             # conditions of use
    "termini e condizioni",         # terms and conditions
    "politica dei cookie",          # cookie policy
    "utilizziamo i cookie",         # we use cookies
    "questo sito utilizza cookie",  # this site uses cookies
    "tutti i diritti riservati",    # all rights reserved
    "diritti riservati",            # rights reserved
    "copyright",                    # copyright
    "iscriviti alla newsletter",    # subscribe to newsletter
    "newsletter",                   # newsletter
    "inserisci la tua email",       # enter your email
    "inserisci il tuo indirizzo",   # enter your address
    "accedi",                       # login
    "accesso",                      # access/login
    "crea un account",              # create account
    "registrati",                   # register
    "password dimenticata",         # forgot password
    "seguici su",                   # follow us on
    "social media",                 # social media
    "articoli correlati",           # related articles
    "potrebbe interessarti",        # you might be interested
    "leggi tutto",                  # read all
    "continua a leggere",           # continue reading
    "lascia un commento",           # leave a comment
    "commenti chiusi",              # comments closed
    "aggiungi al carrello",         # add to cart
    "acquista ora",                 # buy now
]

ITALIAN_PLACEHOLDER_PATTERNS = [
    "questo è un esempio",          # this is an example
    "testo di prova",               # test text
    "testo di esempio",             # example text
    "lorem ipsum",                  # lorem ipsum
]

ITALIAN_CITATION_REGEX = re.compile(
    r'\[\d+\]|\[edit\]|\[citation needed\]|\[modifica\]|\[senza fonte\]|\[citazione necessaria\]'
)

# Italian laughter and expression patterns
ITALIAN_REPETITION_PATTERNS = re.compile(
    r'[ah]{4,}|'        # ahahahah (laughter)
    r'[ha]{4,}|'        # hahahaha (laughter)
    r'[eh]{4,}|'        # eheheheh (laughter)
    r'[he]{4,}|'        # hehehehe (laughter)
    r'[oh]{4,}|'        # ohohohoh (exclamation)
    r'[ho]{4,}'         # hohohoho (exclamation)
)


# =============================================================================
# Thai Configuration
# =============================================================================
# Thai uses its own script (U+0E00-U+0E7F)
THAI_SCRIPT_RANGE = re.compile(
    r'[\u0E00-\u0E7F]'  # Thai script block
)

THAI_TERMINAL_PUNCTUATION = (
    # Thai punctuation marks
    '\u0E2F',  # ฯ Thai character PAIYANNOI (abbreviation)
    '\u0E5A',  # ๚ Thai character ANGKHANKHU (end of verse)
    '\u0E5B',  # ๛ Thai character KHOMUT (end of chapter)
    # Latin punctuation (commonly used in Thai web text)
    '.', '!', '?', '"', "'",
    ':', ';', ')', ']',
    '\u00BB',  # »
    '\u201D',  # "
    '\u2019',  # '
)

THAI_POLICY_PHRASES = [
    "นโยบายความเป็นส่วนตัว",          # privacy policy
    "นโยบายคุ้มครองข้อมูลส่วนบุคคล",    # personal data protection policy
    "ข้อกำหนดการใช้งาน",              # terms of use
    "ข้อกำหนดและเงื่อนไข",            # terms and conditions
    "เงื่อนไขการใช้บริการ",            # terms of service
    "นโยบายคุกกี้",                   # cookie policy
    "เว็บไซต์นี้ใช้คุกกี้",            # this website uses cookies
    "สงวนลิขสิทธิ์",                  # all rights reserved
    "ลิขสิทธิ์",                      # copyright
    "สมัครรับข่าวสาร",                # subscribe to newsletter
    "กรอกอีเมล",                     # enter email
    "เข้าสู่ระบบ",                    # login
    "ลงทะเบียน",                     # register
    "สมัครสมาชิก",                   # sign up
    "ลืมรหัสผ่าน",                    # forgot password
    "ติดตามเรา",                     # follow us
    "แชร์บน",                        # share on
    "อ่านเพิ่มเติม",                  # read more
    "บทความที่เกี่ยวข้อง",            # related articles
    "แสดงความคิดเห็น",               # leave a comment
    "ปิดความคิดเห็น",                # comments closed
]

THAI_PLACEHOLDER_PATTERNS = [
    "นี่คือตัวอย่าง",                 # this is an example
    "ข้อความทดสอบ",                  # test text
    "ข้อความตัวอย่าง",               # sample text
]

THAI_CITATION_REGEX = re.compile(
    r'\[\d+\]|\[edit\]|\[citation needed\]|\[แก้ไข\]|\[ต้องการอ้างอิง\]'
)

# Thai laughter and expression patterns
# Thai people commonly use "555" (5 in Thai = "ha", so 555 = hahaha)
THAI_REPETITION_PATTERNS = re.compile(
    r'5{4,}|'           # 5555 (Thai laughter - "ha ha ha ha")
    r'ก{4,}|'           # กกกก (exclamation)
    r'ค{4,}|'           # คคคค (exclamation)
    r'จ{4,}|'           # จจจจ (laughter variant)
    r'ฮ{4,}'            # ฮฮฮฮ (laughter)
)


# =============================================================================
# Consolidated Language Configuration
# =============================================================================
LANGUAGE_CONFIG = {
    "ar": {
        "script_range": ARABIC_SCRIPT_RANGE,
        "terminal_punctuation": ARABIC_TERMINAL_PUNCTUATION,
        "policy_phrases": ARABIC_POLICY_PHRASES,
        "placeholder_patterns": ARABIC_PLACEHOLDER_PATTERNS,
        "citation_regex": ARABIC_CITATION_REGEX,
        "repetition_patterns": ARABIC_REPETITION_PATTERNS,
    },
    "tr": {
        "script_range": TURKISH_SCRIPT_RANGE,
        "terminal_punctuation": TURKISH_TERMINAL_PUNCTUATION,
        "policy_phrases": TURKISH_POLICY_PHRASES,
        "placeholder_patterns": TURKISH_PLACEHOLDER_PATTERNS,
        "citation_regex": TURKISH_CITATION_REGEX,
        "repetition_patterns": TURKISH_REPETITION_PATTERNS,
        # Additional Turkish-specific config
        "specific_chars": TURKISH_SPECIFIC_CHARS,
    },
    "hi": {
        "script_range": HINDI_SCRIPT_RANGE,
        "terminal_punctuation": HINDI_TERMINAL_PUNCTUATION,
        "policy_phrases": HINDI_POLICY_PHRASES,
        "placeholder_patterns": HINDI_PLACEHOLDER_PATTERNS,
        "citation_regex": HINDI_CITATION_REGEX,
        "repetition_patterns": HINDI_REPETITION_PATTERNS,
    },
    "it": {
        "script_range": ITALIAN_SCRIPT_RANGE,
        "terminal_punctuation": ITALIAN_TERMINAL_PUNCTUATION,
        "policy_phrases": ITALIAN_POLICY_PHRASES,
        "placeholder_patterns": ITALIAN_PLACEHOLDER_PATTERNS,
        "citation_regex": ITALIAN_CITATION_REGEX,
        "repetition_patterns": ITALIAN_REPETITION_PATTERNS,
        # Additional Italian-specific config
        "specific_chars": ITALIAN_SPECIFIC_CHARS,
    },
    "th": {
        "script_range": THAI_SCRIPT_RANGE,
        "terminal_punctuation": THAI_TERMINAL_PUNCTUATION,
        "policy_phrases": THAI_POLICY_PHRASES,
        "placeholder_patterns": THAI_PLACEHOLDER_PATTERNS,
        "citation_regex": THAI_CITATION_REGEX,
        "repetition_patterns": THAI_REPETITION_PATTERNS,
    },
}
