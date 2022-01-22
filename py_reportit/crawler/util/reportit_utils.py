import re
import pytz

from textwrap import TextWrapper
from typing import Callable
from unicodedata import normalize
from datetime import datetime, timedelta
from random import choices

from py_reportit.shared.model.answer_meta import ReportAnswerMeta
from py_reportit.shared.model.answer_meta_tweet import AnswerMetaTweet
from py_reportit.shared.model.report_answer import ReportAnswer
from py_reportit.shared.model.meta_tweet import MetaTweet
from py_reportit.shared.model.meta import Meta
from py_reportit.shared.model.report import Report

def extract_ids(reports: list[Report]) -> list[int]:
    return list(map(lambda report: report.id, reports))

def filter_reports_by_state(reports: list[Report], finished: bool) -> list[Report]:
    return list(filter(lambda report: report.status == 'finished' if finished else 'accepted', reports))

def truncate_float(f: float, decimals: int) -> float:
    return int(f*10**decimals)/10**decimals

def reports_are_roughly_equal_by_position(r1: Report, r2: Report, decimals: int) -> bool:
    return positions_are_rougly_equal(r1.latitude, r1.longitude, r2.latitude, r2.longitude, decimals)

def positions_are_rougly_equal(lat1: float or str, lon1: float or str, lat2: float or str, lon2: float or str, decimals: int) -> bool:
    lats_are_equal = truncate_float(float(lat1), decimals) == truncate_float(float(lat2), decimals)
    lons_are_equal = truncate_float(float(lon1), decimals) == truncate_float(float(lon2), decimals)

    return lats_are_equal and lons_are_equal

def get_last_tweet_id(report: Report) -> str:
    if report.answers and len(report.answers):
        all_answers: list[ReportAnswer] = report.answers
        all_answers_with_tweet_ids = list(filter(lambda answer: answer.meta.tweet_ids and len(answer.meta.tweet_ids), all_answers))

        if len(all_answers_with_tweet_ids):
            newest_answer = max(all_answers_with_tweet_ids, key=lambda answer: answer.order)
            answer_meta: ReportAnswerMeta = newest_answer.meta
            tweet_ids: list[AnswerMetaTweet] = answer_meta.tweet_ids

            partial_closure_tweet_ids = list(filter(lambda tweet_id: tweet_id.type == "partial_closure", tweet_ids))

            if len(partial_closure_tweet_ids):
                return max(partial_closure_tweet_ids, key=lambda tweet_id: tweet_id.order).tweet_id

            return max(tweet_ids, key=lambda tweet_id: tweet_id.order).tweet_id

    report_meta: Meta = report.meta

    if report_meta.tweet_ids:
        tweet_ids: list[MetaTweet] = report_meta.tweet_ids
        follow_tweet_id = next(filter(lambda tweet_id: tweet_id.type == "follow", tweet_ids), False)

        if follow_tweet_id:
            return follow_tweet_id.tweet_id

        return max(tweet_ids, key=lambda tweet_id: tweet_id.order).tweet_id

    return None

# Adapted from https://www.geeksforgeeks.org/python-generate-k-random-dates-between-two-other-dates/
def generate_random_times_between(start: datetime, end: datetime, amount: int) -> list[datetime]:
    result_datetimes = [start]

    current_datetime = start

    while current_datetime != end:
        current_datetime += timedelta(seconds=1)
        result_datetimes.append(current_datetime)

    return sorted(choices(result_datetimes, k=amount))

def to_utc(dtime: datetime) -> datetime:
    lu_tz = pytz.timezone('Europe/Luxembourg')
    lu_dt = lu_tz.localize(dtime)
    return lu_dt.astimezone(pytz.UTC)

format_time: Callable[[datetime], str] = lambda dtime: dtime.strftime("%Y/%m/%d %H:%M:%S")

# The following constants come from python-twitter
# https://github.com/bear/python-twitter/blob/master/twitter/twitter_utils.py
CHAR_RANGES = [
    range(0, 4351),
    range(8192, 8205),
    range(8208, 8223),
    range(8242, 8247)]

TLDS = [
    "ac", "ad", "ae", "af", "ag", "ai", "al", "am", "an", "ao", "aq", "ar",
    "as", "at", "au", "aw", "ax", "az", "ba", "bb", "bd", "be", "bf", "bg",
    "bh", "bi", "bj", "bl", "bm", "bn", "bo", "bq", "br", "bs", "bt", "bv",
    "bw", "by", "bz", "ca", "cc", "cd", "cf", "cg", "ch", "ci", "ck", "cl",
    "cm", "cn", "co", "cr", "cu", "cv", "cw", "cx", "cy", "cz", "de", "dj",
    "dk", "dm", "do", "dz", "ec", "ee", "eg", "eh", "er", "es", "et", "eu",
    "fi", "fj", "fk", "fm", "fo", "fr", "ga", "gb", "gd", "ge", "gf", "gg",
    "gh", "gi", "gl", "gm", "gn", "gp", "gq", "gr", "gs", "gt", "gu", "gw",
    "gy", "hk", "hm", "hn", "hr", "ht", "hu", "id", "ie", "il", "im", "in",
    "io", "iq", "ir", "is", "it", "je", "jm", "jo", "jp", "ke", "kg", "kh",
    "ki", "km", "kn", "kp", "kr", "kw", "ky", "kz", "la", "lb", "lc", "li",
    "lk", "lr", "ls", "lt", "lu", "lv", "ly", "ma", "mc", "md", "me", "mf",
    "mg", "mh", "mk", "ml", "mm", "mn", "mo", "mp", "mq", "mr", "ms", "mt",
    "mu", "mv", "mw", "mx", "my", "mz", "na", "nc", "ne", "nf", "ng", "ni",
    "nl", "no", "np", "nr", "nu", "nz", "om", "pa", "pe", "pf", "pg", "ph",
    "pk", "pl", "pm", "pn", "pr", "ps", "pt", "pw", "py", "qa", "re", "ro",
    "rs", "ru", "rw", "sa", "sb", "sc", "sd", "se", "sg", "sh", "si", "sj",
    "sk", "sl", "sm", "sn", "so", "sr", "ss", "st", "su", "sv", "sx", "sy",
    "sz", "tc", "td", "tf", "tg", "th", "tj", "tk", "tl", "tm", "tn", "to",
    "tp", "tr", "tt", "tv", "tw", "tz", "ua", "ug", "uk", "um", "us", "uy",
    "uz", "va", "vc", "ve", "vg", "vi", "vn", "vu", "wf", "ws", "ye", "yt",
    "za", "zm", "zw", "ελ", "бел", "мкд", "мон", "рф", "срб", "укр", "қаз",
    "հայ", "الاردن", "الجزائر", "السعودية", "المغرب", "امارات", "ایران", "بھارت",
    "تونس", "سودان", "سورية", "عراق", "عمان", "فلسطين", "قطر", "مصر",
    "مليسيا", "پاکستان", "भारत", "বাংলা", "ভারত", "ਭਾਰਤ", "ભારત",
    "இந்தியா", "இலங்கை", "சிங்கப்பூர்", "భారత్", "ලංකා", "ไทย",
    "გე", "中国", "中國", "台湾", "台灣", "新加坡", "澳門", "香港", "한국", "neric:",
    "abb", "abbott", "abogado", "academy", "accenture", "accountant",
    "accountants", "aco", "active", "actor", "ads", "adult", "aeg", "aero",
    "afl", "agency", "aig", "airforce", "airtel", "allfinanz", "alsace",
    "amsterdam", "android", "apartments", "app", "aquarelle", "archi", "army",
    "arpa", "asia", "associates", "attorney", "auction", "audio", "auto",
    "autos", "axa", "azure", "band", "bank", "bar", "barcelona", "barclaycard",
    "barclays", "bargains", "bauhaus", "bayern", "bbc", "bbva", "bcn", "beer",
    "bentley", "berlin", "best", "bet", "bharti", "bible", "bid", "bike",
    "bing", "bingo", "bio", "biz", "black", "blackfriday", "bloomberg", "blue",
    "bmw", "bnl", "bnpparibas", "boats", "bond", "boo", "boots", "boutique",
    "bradesco", "bridgestone", "broker", "brother", "brussels", "budapest",
    "build", "builders", "business", "buzz", "bzh", "cab", "cafe", "cal",
    "camera", "camp", "cancerresearch", "canon", "capetown", "capital",
    "caravan", "cards", "care", "career", "careers", "cars", "cartier",
    "casa", "cash", "casino", "cat", "catering", "cba", "cbn", "ceb", "center",
    "ceo", "cern", "cfa", "cfd", "chanel", "channel", "chat", "cheap",
    "chloe", "christmas", "chrome", "church", "cisco", "citic", "city",
    "claims", "cleaning", "click", "clinic", "clothing", "cloud", "club",
    "coach", "codes", "coffee", "college", "cologne", "com", "commbank",
    "community", "company", "computer", "condos", "construction", "consulting",
    "contractors", "cooking", "cool", "coop", "corsica", "country", "coupons",
    "courses", "credit", "creditcard", "cricket", "crown", "crs", "cruises",
    "cuisinella", "cymru", "cyou", "dabur", "dad", "dance", "date", "dating",
    "datsun", "day", "dclk", "deals", "degree", "delivery", "delta",
    "democrat", "dental", "dentist", "desi", "design", "dev", "diamonds",
    "diet", "digital", "direct", "directory", "discount", "dnp", "docs",
    "dog", "doha", "domains", "doosan", "download", "drive", "durban", "dvag",
    "earth", "eat", "edu", "education", "email", "emerck", "energy",
    "engineer", "engineering", "enterprises", "epson", "equipment", "erni",
    "esq", "estate", "eurovision", "eus", "events", "everbank", "exchange",
    "expert", "exposed", "express", "fage", "fail", "faith", "family", "fan",
    "fans", "farm", "fashion", "feedback", "film", "finance", "financial",
    "firmdale", "fish", "fishing", "fit", "fitness", "flights", "florist",
    "flowers", "flsmidth", "fly", "foo", "football", "forex", "forsale",
    "forum", "foundation", "frl", "frogans", "fund", "furniture", "futbol",
    "fyi", "gal", "gallery", "game", "garden", "gbiz", "gdn", "gent",
    "genting", "ggee", "gift", "gifts", "gives", "giving", "glass", "gle",
    "global", "globo", "gmail", "gmo", "gmx", "gold", "goldpoint", "golf",
    "goo", "goog", "google", "gop", "gov", "graphics", "gratis", "green",
    "gripe", "group", "guge", "guide", "guitars", "guru", "hamburg", "hangout",
    "haus", "healthcare", "help", "here", "hermes", "hiphop", "hitachi", "hiv",
    "hockey", "holdings", "holiday", "homedepot", "homes", "honda", "horse",
    "host", "hosting", "hoteles", "hotmail", "house", "how", "hsbc", "ibm",
    "icbc", "ice", "icu", "ifm", "iinet", "immo", "immobilien", "industries",
    "infiniti", "info", "ing", "ink", "institute", "insure", "int",
    "international", "investments", "ipiranga", "irish", "ist", "istanbul",
    "itau", "iwc", "java", "jcb", "jetzt", "jewelry", "jlc", "jll", "jobs",
    "joburg", "jprs", "juegos", "kaufen", "kddi", "kim", "kitchen", "kiwi",
    "koeln", "komatsu", "krd", "kred", "kyoto", "lacaixa", "lancaster", "land",
    "lasalle", "lat", "latrobe", "law", "lawyer", "lds", "lease", "leclerc",
    "legal", "lexus", "lgbt", "liaison", "lidl", "life", "lighting", "limited",
    "limo", "link", "live", "lixil", "loan", "loans", "lol", "london", "lotte",
    "lotto", "love", "ltda", "lupin", "luxe", "luxury", "madrid", "maif",
    "maison", "man", "management", "mango", "market", "marketing", "markets",
    "marriott", "mba", "media", "meet", "melbourne", "meme", "memorial", "men",
    "menu", "miami", "microsoft", "mil", "mini", "mma", "mobi", "moda", "moe",
    "mom", "monash", "money", "montblanc", "mormon", "mortgage", "moscow",
    "motorcycles", "mov", "movie", "movistar", "mtn", "mtpc", "museum",
    "nadex", "nagoya", "name", "navy", "nec", "net", "netbank", "network",
    "neustar", "new", "news", "nexus", "ngo", "nhk", "nico", "ninja", "nissan",
    "nokia", "nra", "nrw", "ntt", "nyc", "office", "okinawa", "omega", "one",
    "ong", "onl", "online", "ooo", "oracle", "orange", "org", "organic",
    "osaka", "otsuka", "ovh", "page", "panerai", "paris", "partners", "parts",
    "party", "pet", "pharmacy", "philips", "photo", "photography", "photos",
    "physio", "piaget", "pics", "pictet", "pictures", "pink", "pizza", "place",
    "play", "plumbing", "plus", "pohl", "poker", "porn", "post", "praxi",
    "press", "pro", "prod", "productions", "prof", "properties", "property",
    "pub", "qpon", "quebec", "racing", "realtor", "realty", "recipes", "red",
    "redstone", "rehab", "reise", "reisen", "reit", "ren", "rent", "rentals",
    "repair", "report", "republican", "rest", "restaurant", "review",
    "reviews", "rich", "ricoh", "rio", "rip", "rocks", "rodeo", "rsvp", "ruhr",
    "run", "ryukyu", "saarland", "sakura", "sale", "samsung", "sandvik",
    "sandvikcoromant", "sanofi", "sap", "sarl", "saxo", "sca", "scb",
    "schmidt", "scholarships", "school", "schule", "schwarz", "science",
    "scor", "scot", "seat", "seek", "sener", "services", "sew", "sex", "sexy",
    "shiksha", "shoes", "show", "shriram", "singles", "site", "ski", "sky",
    "skype", "sncf", "soccer", "social", "software", "sohu", "solar",
    "solutions", "sony", "soy", "space", "spiegel", "spreadbetting", "srl",
    "starhub", "statoil", "studio", "study", "style", "sucks", "supplies",
    "supply", "support", "surf", "surgery", "suzuki", "swatch", "swiss",
    "sydney", "systems", "taipei", "tatamotors", "tatar", "tattoo", "tax",
    "taxi", "team", "tech", "technology", "tel", "telefonica", "temasek",
    "tennis", "thd", "theater", "tickets", "tienda", "tips", "tires", "tirol",
    "today", "tokyo", "tools", "top", "toray", "toshiba", "tours", "town",
    "toyota", "toys", "trade", "trading", "training", "travel", "trust", "tui",
    "ubs", "university", "uno", "uol", "vacations", "vegas", "ventures",
    "vermögensberater", "vermögensberatung", "versicherung", "vet", "viajes",
    "video", "villas", "vin", "vision", "vista", "vistaprint", "vlaanderen",
    "vodka", "vote", "voting", "voto", "voyage", "wales", "walter", "wang",
    "watch", "webcam", "website", "wed", "wedding", "weir", "whoswho", "wien",
    "wiki", "williamhill", "win", "windows", "wine", "wme", "work", "works",
    "world", "wtc", "wtf", "xbox", "xerox", "xin", "xperia", "xxx", "xyz",
    "yachts", "yandex", "yodobashi", "yoga", "yokohama", "youtube", "zip",
    "zone", "zuerich", "дети", "ком", "москва", "онлайн", "орг", "рус", "сайт",
    "קום", "بازار", "شبكة", "كوم", "موقع", "कॉम", "नेट", "संगठन", "คอม",
    "みんな", "グーグル", "コム", "世界", "中信", "中文网", "企业", "佛山", "信息",
    "健康", "八卦", "公司", "公益", "商城", "商店", "商标", "在线", "大拿", "娱乐",
    "工行", "广东", "慈善", "我爱你", "手机", "政务", "政府", "新闻", "时尚", "机构",
    "淡马锡", "游戏", "点看", "移动", "组织机构", "网址", "网店", "网络", "谷歌", "集团",
    "飞利浦", "餐厅", "닷넷", "닷컴", "삼성", "onion"]

URL_REGEXP = re.compile((
    r'('
    r'^(?!(https?://|www\.)?\.|ftps?://|([0-9]+\.){{1,3}}\d+)'  # exclude urls that start with "."
    r'(?:https?://|www\.)*^(?!.*@)(?:[\w+-_]+[.])'              # beginning of url
    r'(?:{0}\b'                                                 # all tlds
    r'(?:[:0-9]))'                                              # port numbers & close off TLDs
    r'(?:[\w+\/]?[a-z0-9!\*\'\(\);:&=\+\$/%#\[\]\-_\.,~?])*'    # path/query params
    r')').format(r'\b|'.join(TLDS)), re.U | re.I | re.X)

# The following function comes from python-twitter, and has been slightly modified
# https://github.com/bear/python-twitter/blob/master/twitter/twitter_utils.py
def calc_expected_status_length(status: str or bytes, short_url_length: int = 23) -> int:
    """Calculate the length of a tweet.
    Takes into account Twitter's replacement of URLs with https://t.co links.
    Args:
        status: text of the status message to be posted.
        short_url_length: the current published https://t.co links
    Returns:
        Expected length of the status message as an integer.
    """
    status_length = 0
    if isinstance(status, bytes):
        status = str(status)
    for word in re.split(r'\s', status):
        if is_url(word):
            status_length += short_url_length
        else:
            for character in word:
                if any([ord(normalize("NFC", character)) in char_range for char_range in CHAR_RANGES]):
                    status_length += 1
                else:
                    status_length += 2
    status_length += len(re.findall(r'\s', status))
    return status_length

# The following function comes from python-twitter, and has been slightly modified
# https://github.com/bear/python-twitter/blob/master/twitter/twitter_utils.py
def is_url(text) -> bool:
    """Check to see if a bit of text is a URL.
    Args:
        text: text to check.
    Returns:
        Boolean of whether the text should be treated as a URL or not.
    """
    return bool(re.findall(URL_REGEXP, text))

class TwitterWrapper(TextWrapper):

    def _handle_long_word(self, reversed_chunks, cur_line, cur_len, width):
        """_handle_long_word(chunks : [string],
                             cur_line : [string],
                             cur_len : int, width : int)
        Handle a chunk of text (most likely a word, not whitespace) that
        is too long to fit in any line.
        """
        # Figure out when indent is larger than the specified width, and make
        # sure at least one character is stripped off on every pass
        if width < 1:
            space_left = 1
        else:
            space_left = width - cur_len

        # If we're allowed to break long words, then do so: put as much
        # of the next chunk onto the current line as will fit.
        if self.break_long_words:
            end = space_left
            chunk = reversed_chunks[-1]
            if self.break_on_hyphens and calc_expected_status_length(chunk) > space_left:
                # break after last hyphen, but only if there are
                # non-hyphens before it
                hyphen = chunk.rfind('-', 0, space_left)
                if hyphen > 0 and any(c != '-' for c in chunk[:hyphen]):
                    end = hyphen + 1
            cur_line.append(chunk[:end])
            reversed_chunks[-1] = chunk[end:]

        # Otherwise, we have to preserve the long word intact.  Only add
        # it to the current line if there's nothing already there --
        # that minimizes how much we violate the width constraint.
        elif not cur_line:
            cur_line.append(reversed_chunks.pop())

        # If we're not allowed to break long words, and there's already
        # text on the current line, do nothing.  Next time through the
        # main loop of _wrap_chunks(), we'll wind up here again, but
        # cur_len will be zero, so the next line will be entirely
        # devoted to the long word that we can't handle right now.

    def _wrap_chunks(self, chunks):
        """_wrap_chunks(chunks : [string]) -> [string]
        Wrap a sequence of text chunks and return a list of lines of
        length 'self.width' or less.  (If 'break_long_words' is false,
        some lines may be longer than this.)  Chunks correspond roughly
        to words and the whitespace between them: each chunk is
        indivisible (modulo 'break_long_words'), but a line break can
        come between any two chunks.  Chunks should not have internal
        whitespace; ie. a chunk is either all whitespace or a "word".
        Whitespace chunks will be removed from the beginning and end of
        lines, but apart from that whitespace is preserved.
        """
        lines = []
        if self.width <= 0:
            raise ValueError("invalid width %r (must be > 0)" % self.width)
        if self.max_lines is not None:
            if self.max_lines > 1:
                indent = self.subsequent_indent
            else:
                indent = self.initial_indent
            if len(indent) + len(self.placeholder.lstrip()) > self.width:
                raise ValueError("placeholder too large for max width")

        # Arrange in reverse order so items can be efficiently popped
        # from a stack of chucks.
        chunks.reverse()

        while chunks:

            # Start the list of chunks that will make up the current line.
            # cur_len is just the length of all the chunks in cur_line.
            cur_line = []
            cur_len = 0

            # Figure out which static string will prefix this line.
            if lines:
                indent = self.subsequent_indent
            else:
                indent = self.initial_indent

            # Maximum width for this line.
            width = self.width - len(indent)

            # First chunk on line is whitespace -- drop it, unless this
            # is the very beginning of the text (ie. no lines started yet).
            if self.drop_whitespace and chunks[-1].strip() == '' and lines:
                del chunks[-1]

            while chunks:
                l = calc_expected_status_length(chunks[-1])

                # Can at least squeeze this chunk onto the current line.
                if cur_len + l <= width:
                    cur_line.append(chunks.pop())
                    cur_len += l

                # Nope, this line is full.
                else:
                    break

            # The current line is full, and the next chunk is too big to
            # fit on *any* line (not just this one).
            if chunks and calc_expected_status_length(chunks[-1]) > width:
                self._handle_long_word(chunks, cur_line, cur_len, width)
                cur_len = sum(map(calc_expected_status_length, cur_line))

            # If the last chunk on this line is all whitespace, drop it.
            if self.drop_whitespace and cur_line and cur_line[-1].strip() == '':
                cur_len -= calc_expected_status_length(cur_line[-1])
                del cur_line[-1]

            if cur_line:
                if (self.max_lines is None or
                    len(lines) + 1 < self.max_lines or
                    (not chunks or
                     self.drop_whitespace and
                     len(chunks) == 1 and
                     not chunks[0].strip()) and cur_len <= width):
                    # Convert current line back to a string and store it in
                    # list of all lines (return value).
                    lines.append(indent + ''.join(cur_line))
                else:
                    while cur_line:
                        if (cur_line[-1].strip() and
                            cur_len + len(self.placeholder) <= width):
                            cur_line.append(self.placeholder)
                            lines.append(indent + ''.join(cur_line))
                            break
                        cur_len -= calc_expected_status_length(cur_line[-1])
                        del cur_line[-1]
                    else:
                        if lines:
                            prev_line = lines[-1].rstrip()
                            if (calc_expected_status_length(prev_line) + len(self.placeholder) <=
                                    self.width):
                                lines[-1] = prev_line + self.placeholder
                                break
                        lines.append(indent + self.placeholder.lstrip())
                    break

        return lines

def twitter_wrap(text, width=280, **kwargs):
    """Wrap a single paragraph of text, returning a list of wrapped lines.
    Reformat the single paragraph in 'text' so it fits in lines of no
    more than 'width' columns, and return a list of wrapped lines.  By
    default, tabs in 'text' are expanded with string.expandtabs(), and
    all other whitespace characters (including newline) are converted to
    space.  See TextWrapper class for available keyword args to customize
    wrapping behaviour.
    """
    w = TwitterWrapper(width=width, **kwargs)
    return w.wrap(text)