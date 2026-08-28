"""Message catalog: finding id -> human text, per language.

This is the only file with prose in it. Checks emit ids and params; the report
resolves them here. Adding a language means adding a key, not touching a check.

Tone rules (docs/report-tone): proportionate, specific, no drama. A missing
header is described as missing, not as a risk to the business.
"""

from __future__ import annotations

from .models import Finding

LANGUAGES = ("en", "bg")
DEFAULT_LANGUAGE = "en"

DISCLAIMER = {
    "en": (
        "This is a public, non-intrusive website health assessment. "
        "Deeper security testing requires authorization."
    ),
    "bg": (
        "Това е публична, неинвазивна проверка на състоянието на уебсайта. "
        "По-задълбочено тестване на сигурността изисква изрично разрешение."
    ),
}

HEADINGS = {
    "en": {
        "report_title": "Website Health Check",
        "overall": "Overall",
        "working": "Working well",
        "attention": "Worth looking at",
        "detected": "Detected",
        "not_checked": "Not checked",
        "prospect": "Prospect score",
        "scanned_at": "Checked on",
        "prepared_by": "Prepared by Viridian Grids",
        "inconclusive": (
            "This site blocked our automated request, so this check is incomplete "
            "and should not be sent as-is."
        ),
    },
    "bg": {
        "report_title": "Проверка на състоянието на сайта",
        "overall": "Обща оценка",
        "working": "Работи добре",
        "attention": "Заслужава внимание",
        "detected": "Открито",
        "not_checked": "Непроверено",
        "prospect": "Оценка на потенциала",
        "scanned_at": "Проверено на",
        "prepared_by": "Изготвено от Viridian Grids",
        "inconclusive": (
            "Този сайт блокира автоматичната ни заявка, затова проверката е непълна "
            "и не бива да се изпраща в този вид."
        ),
    },
}

BANDS = {
    "en": {"good": "Good", "fair": "Needs some attention", "poor": "Needs attention"},
    "bg": {"good": "Добро", "fair": "Има какво да се подобри", "poor": "Нуждае се от внимание"},
}

CATEGORY_NAMES = {
    "en": {
        "availability": "Availability",
        "tls": "Certificate & encryption",
        "http": "Security headers",
        "cookies": "Cookies",
        "technology": "Technology",
        "configuration": "Configuration",
        "performance": "Performance",
    },
    "bg": {
        "availability": "Достъпност",
        "tls": "Сертификат и криптиране",
        "http": "HTTP Headers за сигурност",
        "cookies": "Бисквитки",
        "technology": "Технологии",
        "configuration": "Конфигурация",
        "performance": "Производителност",
    },
}

# id -> language -> (title, detail template)
MESSAGES: dict[str, dict[str, tuple[str, str]]] = {
    # ---------------------------------------------------------------- availability
    "availability.unreachable": {
        "en": ("Website did not respond", "No response over HTTPS or HTTP ({error})."),
        "bg": ("Сайтът не отговори", "Няма отговор нито по HTTPS, нито по HTTP ({error})."),
    },
    "availability.dns_failure": {
        "en": (
            "The domain does not resolve",
            "There is no DNS record for it ({error}). The domain has most likely lapsed.",
        ),
        "bg": (
            "Домейнът не се резолвва",
            "Няма DNS запис за него ({error}). Най-вероятно домейнът е изтекъл.",
        ),
    },
    "availability.reachable": {
        "en": ("Website is reachable", "Responded at {url}."),
        "bg": ("Сайтът е достъпен", "Отговори на {url}."),
    },
    "availability.https_ok": {
        "en": ("HTTPS is working", "The site is served over an encrypted connection."),
        "bg": ("HTTPS работи", "Сайтът се обслужва по криптирана връзка."),
    },
    "availability.https_unavailable": {
        "en": (
            "HTTPS is not available",
            "The site answers over plain HTTP only ({error}). Browsers will mark it as not secure.",
        ),
        "bg": (
            "HTTPS не е достъпен",
            "Сайтът отговаря само по обикновен HTTP ({error}). Браузърите го маркират като несигурен.",
        ),
    },
    "availability.request_blocked": {
        "en": (
            "The site refused our automated request",
            "It answered HTTP {status}, which usually means bot protection. "
            "The rest of this check is therefore incomplete.",
        ),
        "bg": (
            "Сайтът отказа автоматичната ни заявка",
            "Отговори с HTTP {status}, което обикновено означава защита срещу ботове. "
            "Затова останалата част от проверката е непълна.",
        ),
    },
    "availability.status_ok": {
        "en": ("Homepage returns a normal response", "HTTP status {status}."),
        "bg": ("Началната страница отговаря нормално", "HTTP статус {status}."),
    },
    "availability.status_redirect": {
        "en": ("Homepage still redirects", "The final response was a redirect (HTTP {status})."),
        "bg": (
            "Началната страница все още пренасочва",
            "Крайният отговор беше пренасочване (HTTP {status}).",
        ),
    },
    "availability.status_error": {
        "en": ("Homepage returns an error", "HTTP status {status}."),
        "bg": ("Началната страница връща грешка", "HTTP статус {status}."),
    },
    # ------------------------------------------------------------------------ tls
    "tls.unavailable": {
        "en": ("Certificate could not be checked", "No TLS handshake was possible ({error})."),
        "bg": ("Сертификатът не можа да бъде проверен", "TLS връзка не беше възможна ({error})."),
    },
    "tls.certificate_trusted": {
        "en": ("Certificate is valid", "Issued by {issuer} and trusted by browsers."),
        "bg": ("Сертификатът е валиден", "Издаден от {issuer} и се доверява от браузърите."),
    },
    "tls.certificate_untrusted": {
        "en": (
            "Certificate is not trusted by browsers",
            "Visitors will see a security warning ({reason}).",
        ),
        "bg": (
            "Сертификатът не се приема от браузърите",
            "Посетителите ще виждат предупреждение за сигурност ({reason}).",
        ),
    },
    "tls.hostname_mismatch": {
        "en": (
            "Certificate does not cover this domain",
            "It is issued for {names}, which does not match this address.",
        ),
        "bg": (
            "Сертификатът не покрива този домейн",
            "Издаден е за {names}, което не съвпада с този адрес.",
        ),
    },
    "tls.certificate_expired": {
        "en": ("Certificate has expired", "It expired {days} days ago, on {expires}."),
        "bg": ("Сертификатът е изтекъл", "Изтекъл е преди {days} дни, на {expires}."),
    },
    "tls.certificate_expiring_urgently": {
        "en": ("Certificate expires very soon", "{days} days remaining (expires {expires})."),
        "bg": ("Сертификатът изтича много скоро", "Остават {days} дни (изтича на {expires})."),
    },
    "tls.certificate_expiring_soon": {
        "en": ("Certificate expires soon", "{days} days remaining (expires {expires})."),
        "bg": ("Сертификатът изтича скоро", "Остават {days} дни (изтича на {expires})."),
    },
    "tls.certificate_auto_renewing": {
        "en": (
            "Certificate renews automatically",
            "{days} days remaining (expires {expires}). The short validity period means "
            "an automated client is renewing it, so no action is needed.",
        ),
        "bg": (
            "Сертификатът се подновява автоматично",
            "Остават {days} дни (изтича на {expires}). Краткият срок на валидност показва, "
            "че се подновява автоматично, така че не се изисква действие.",
        ),
    },
    "tls.certificate_renewal_failing": {
        "en": (
            "Automatic certificate renewal appears to have stopped",
            "This certificate normally renews itself well before now, but only {days} days "
            "remain (expires {expires}). Worth checking before visitors see a warning.",
        ),
        "bg": (
            "Автоматичното подновяване на сертификата изглежда е спряло",
            "Този сертификат обикновено се подновява доста по-рано, но остават само {days} дни "
            "(изтича на {expires}). Струва си да се провери, преди посетителите да видят предупреждение.",
        ),
    },
    "tls.certificate_expiry_ok": {
        "en": ("Certificate has plenty of time left", "{days} days remaining (expires {expires})."),
        "bg": ("Сертификатът е с достатъчен срок", "Остават {days} дни (изтича на {expires})."),
    },
    "tls.protocol_modern": {
        "en": ("Modern encryption in use", "The connection negotiated {version}."),
        "bg": ("Използва се съвременно криптиране", "Връзката договори {version}."),
    },
    "tls.protocol_outdated": {
        "en": ("Outdated encryption in use", "The connection negotiated {version}."),
        "bg": ("Използва се остаряло криптиране", "Връзката договори {version}."),
    },
    "tls.legacy_protocols_disabled": {
        "en": (
            "Old TLS versions are switched off",
            "TLS 1.0 and 1.1 were refused, as they should be.",
        ),
        "bg": ("Старите версии на TLS са изключени", "TLS 1.0 и 1.1 бяха отказани, както трябва."),
    },
    "tls.legacy_protocols_enabled": {
        "en": ("Old TLS versions are still accepted", "The server still accepts {versions}."),
        "bg": ("Все още се приемат стари версии на TLS", "Сървърът все още приема {versions}."),
    },
    "tls.legacy_not_tested": {
        "en": ("Old TLS versions were not tested", "This check was skipped."),
        "bg": ("Старите версии на TLS не бяха тествани", "Проверката беше пропусната."),
    },
    # ---------------------------------------------------- testssl.sh (engine)
    "testssl.tls1": {
        "en": ("TLS 1.0 is still enabled", "An obsolete protocol from 1999 is still accepted."),
        "bg": ("TLS 1.0 все още е включен", "Остарял протокол от 1999 г. все още се приема."),
    },
    "testssl.tls1_1": {
        "en": ("TLS 1.1 is still enabled", "An obsolete protocol is still accepted."),
        "bg": ("TLS 1.1 все още е включен", "Остарял протокол все още се приема."),
    },
    "testssl.beast": {
        "en": (
            "Server is affected by the BEAST weakness",
            "Older CBC ciphers are offered. Modern browsers mitigate it, but the ciphers are worth retiring.",
        ),
        "bg": (
            "Сървърът е засегнат от слабостта BEAST",
            "Предлагат се стари CBC шифри. Съвременните браузъри го смекчават, но шифрите е добре да отпаднат.",
        ),
    },
    "testssl.beast_cbc_tls1": {
        "en": ("Obsolete CBC ciphers offered over TLS 1.0", "Affected ciphers: {finding}"),
        "bg": ("Остарели CBC шифри по TLS 1.0", "Засегнати шифри: {finding}"),
    },
    "testssl.robot": {
        "en": ("Server is vulnerable to the ROBOT attack", "This one is worth fixing promptly."),
        "bg": ("Сървърът е уязвим към атаката ROBOT", "Това си струва да се поправи бързо."),
    },
    "testssl.sweet32": {
        "en": ("64-bit block ciphers offered (SWEET32)", "Legacy 3DES ciphers are still accepted."),
        "bg": (
            "Предлагат се 64-битови блокови шифри (SWEET32)",
            "Все още се приемат стари 3DES шифри.",
        ),
    },
    "testssl.rc4": {
        "en": ("Broken RC4 ciphers offered", "RC4 has been considered broken for over a decade."),
        "bg": (
            "Предлагат се компрометирани RC4 шифри",
            "RC4 се смята за компрометиран над десетилетие.",
        ),
    },
    "testssl.heartbleed": {
        "en": (
            "Server is vulnerable to Heartbleed",
            "Memory can be read remotely. Fix immediately.",
        ),
        "bg": (
            "Сървърът е уязвим към Heartbleed",
            "Паметта може да се чете отдалечено. Поправете незабавно.",
        ),
    },
    "testssl.poodle_ssl": {
        "en": ("Server is vulnerable to POODLE", "SSLv3 is still accepted."),
        "bg": ("Сървърът е уязвим към POODLE", "SSLv3 все още се приема."),
    },
    "testssl.freak": {
        "en": (
            "Export-grade ciphers offered (FREAK)",
            "Deliberately weakened ciphers are accepted.",
        ),
        "bg": ("Предлагат се експортни шифри (FREAK)", "Приемат се умишлено отслабени шифри."),
    },
    "testssl.logjam": {
        "en": ("Weak Diffie-Hellman parameters (LOGJAM)", "Key exchange can be downgraded."),
        "bg": (
            "Слаби Diffie-Hellman параметри (LOGJAM)",
            "Обменът на ключове може да бъде понижен.",
        ),
    },
    "testssl.drown": {
        "en": ("Server is vulnerable to DROWN", "SSLv2 is reachable somewhere on this host."),
        "bg": ("Сървърът е уязвим към DROWN", "SSLv2 е достъпен някъде на този хост."),
    },
    "testssl.secure_renego": {
        "en": ("Insecure TLS renegotiation", "The server allows unsafe renegotiation."),
        "bg": ("Несигурно предоговаряне на TLS", "Сървърът позволява несигурно предоговаряне."),
    },
    # ----------------------------------------------------------------------- http
    "http.headers_not_checked": {
        "en": ("Security headers not checked", "The site did not respond."),
        "bg": ("HTTP Headers за сигурност не са проверени", "Сайтът не отговори."),
    },
    "http.hsts_present": {
        "en": ("HSTS is configured", "Browsers are told to use HTTPS for {days} days."),
        "bg": ("HSTS е настроен", "Браузърите използват HTTPS за {days} дни."),
    },
    "http.hsts_short": {
        "en": (
            "HSTS is configured with a short lifetime",
            "Currently {days} days; six months is the usual minimum.",
        ),
        "bg": (
            "HSTS е настроен с кратък срок",
            "В момента {days} дни; обичайният минимум е шест месеца.",
        ),
    },
    "http.hsts_missing": {
        "en": (
            "HSTS is not configured",
            "Without it, a visitor typing the address can still be sent over plain HTTP first.",
        ),
        "bg": (
            "HSTS не е настроен",
            "Без него посетител, който въведе адреса, може първо да мине по обикновен HTTP.",
        ),
    },
    "http.hsts_not_applicable": {
        "en": ("HSTS not applicable", "The site is not served over HTTPS."),
        "bg": ("HSTS е неприложим", "Сайтът не се обслужва по HTTPS."),
    },
    "http.csp_present": {
        "en": ("Content-Security-Policy is set", "The site restricts where scripts may load from."),
        "bg": (
            "Content-Security-Policy е зададена",
            "Сайтът ограничава откъде може да се зареждат скриптове.",
        ),
    },
    "http.csp_report_only": {
        "en": (
            "Content-Security-Policy is report-only",
            "The policy is monitored but not enforced.",
        ),
        "bg": (
            "Content-Security-Policy е само за докладване",
            "Политиката се следи, но не се прилага.",
        ),
    },
    "http.csp_meta_only": {
        "en": (
            "Content-Security-Policy is set in the page, not the headers",
            "A header is more reliable.",
        ),
        "bg": (
            "Content-Security-Policy е зададена в страницата, не в HTTP Headers",
            "По-надеждно е през HTTP Header.",
        ),
    },
    "http.csp_missing": {
        "en": (
            "Content-Security-Policy is missing",
            "A common hardening step for content-managed sites.",
        ),
        "bg": (
            "Липсва Content-Security-Policy",
            "Обичайна мярка за сайтове с система за управление на съдържание.",
        ),
    },
    "http.xcto_present": {
        "en": ("X-Content-Type-Options is set", "Browsers will not guess file types."),
        "bg": (
            "X-Content-Type-Options е зададена",
            "Браузърите няма да отгатват типа на файловете.",
        ),
    },
    "http.xcto_missing": {
        "en": ("X-Content-Type-Options is missing", "A one-line change on the web server."),
        "bg": ("Липсва X-Content-Type-Options", "Промяна от един ред на уеб сървъра."),
    },
    "http.referrer_policy_present": {
        "en": ("Referrer-Policy is set", "Set to {value}."),
        "bg": ("Referrer-Policy е зададена", "Стойност: {value}."),
    },
    "http.referrer_policy_missing": {
        "en": ("Referrer-Policy is missing", "Controls what address is shared with other sites."),
        "bg": ("Липсва Referrer-Policy", "Контролира какъв адрес се споделя с други сайтове."),
    },
    "http.permissions_policy_present": {
        "en": ("Permissions-Policy is set", "Set to {value}."),
        "bg": ("Permissions-Policy е зададена", "Стойност: {value}."),
    },
    "http.permissions_policy_missing": {
        "en": (
            "Permissions-Policy is missing",
            "Controls access to camera, microphone and location.",
        ),
        "bg": (
            "Липсва Permissions-Policy",
            "Контролира достъпа до камера, микрофон и местоположение.",
        ),
    },
    "http.clickjacking_protected": {
        "en": ("Page cannot be embedded by other sites", "Protected via {via}."),
        "bg": ("Страницата не може да се вгражда в други сайтове", "Защитено чрез {via}."),
    },
    "http.clickjacking_unprotected": {
        "en": (
            "Page can be embedded by other sites",
            "Neither X-Frame-Options nor a CSP frame-ancestors rule is set.",
        ),
        "bg": (
            "Страницата може да се вгражда в други сайтове",
            "Няма нито X-Frame-Options, нито CSP правило frame-ancestors.",
        ),
    },
    # -------------------------------------------------------------------- cookies
    "cookies.not_checked": {
        "en": ("Cookies not checked", "The site did not respond."),
        "bg": ("Бисквитките не са проверени", "Сайтът не отговори."),
    },
    "cookies.none_set": {
        "en": ("No cookies set on the homepage", "Nothing to check here."),
        "bg": ("Началната страница не задава бисквитки", "Няма какво да се провери."),
    },
    "cookies.flags_ok": {
        "en": ("Cookie flags look correct", "All {count} cookies on the homepage are set safely."),
        "bg": (
            "Настройките на бисквитките изглеждат правилни",
            "И {count} бисквитки на началната страница са зададени безопасно.",
        ),
    },
    "cookies.missing_secure": {
        "en": (
            "Some cookies are missing the Secure flag",
            "{count} of {total} homepage cookies ({names}) can be sent over plain HTTP.",
        ),
        "bg": (
            "Някои бисквитки са без флаг Secure",
            "{count} от {total} бисквитки ({names}) могат да се изпращат по обикновен HTTP.",
        ),
    },
    "cookies.missing_httponly": {
        "en": (
            "Some cookies are missing the HttpOnly flag",
            "{count} of {total} homepage cookies ({names}) are readable by JavaScript.",
        ),
        "bg": (
            "Някои бисквитки са без флаг HttpOnly",
            "{count} от {total} бисквитки ({names}) са четими от JavaScript.",
        ),
    },
    "cookies.missing_samesite": {
        "en": (
            "Some cookies are missing the SameSite flag",
            "{count} of {total} homepage cookies ({names}) have no SameSite setting.",
        ),
        "bg": (
            "Някои бисквитки са без флаг SameSite",
            "{count} от {total} бисквитки ({names}) нямат настройка SameSite.",
        ),
    },
    # -------------------------------------------------------------- configuration
    "configuration.http_closed": {
        "en": ("Plain HTTP is not served", "Only HTTPS answers, which is fine."),
        "bg": ("Обикновен HTTP не се обслужва", "Отговаря само HTTPS, което е добре."),
    },
    "configuration.http_redirects_https": {
        "en": ("HTTP redirects to HTTPS", "Permanent redirect (HTTP {status})."),
        "bg": ("HTTP пренасочва към HTTPS", "Постоянно пренасочване (HTTP {status})."),
    },
    "configuration.http_redirects_https_temporary": {
        "en": (
            "HTTP redirects to HTTPS, but temporarily",
            "HTTP {status}; a permanent redirect (301) is the usual choice.",
        ),
        "bg": (
            "HTTP пренасочва към HTTPS, но временно",
            "HTTP {status}; обичайно се използва постоянно пренасочване (301).",
        ),
    },
    "configuration.http_redirects_elsewhere": {
        "en": ("HTTP redirects somewhere unexpected", "It sends visitors to {location}."),
        "bg": ("HTTP пренасочва към неочакван адрес", "Изпраща посетителите към {location}."),
    },
    "configuration.http_no_redirect": {
        "en": (
            "HTTP does not redirect to HTTPS",
            "Visitors on the plain address stay unencrypted (HTTP {status}).",
        ),
        "bg": (
            "HTTP не пренасочва към HTTPS",
            "Посетителите на обикновения адрес остават без криптиране (HTTP {status}).",
        ),
    },
    "configuration.http_error": {
        "en": (
            "The plain HTTP address returns a server error",
            "http:// answers with HTTP {status} instead of redirecting to the secure address.",
        ),
        "bg": (
            "Адресът на обикновен HTTP връща сървърна грешка",
            "http:// отговаря с HTTP {status}, вместо да пренасочва към защитения адрес.",
        ),
    },
    "configuration.redirect_loop": {
        "en": ("Redirect loop detected", "The address keeps redirecting to itself."),
        "bg": ("Открит е цикъл от пренасочвания", "Адресът се пренасочва към себе си."),
    },
    "configuration.redirect_chain_long": {
        "en": ("Long redirect chain", "{hops} redirects before the page loads."),
        "bg": (
            "Дълга верига от пренасочвания",
            "{hops} пренасочвания преди страницата да се зареди.",
        ),
    },
    "configuration.canonical_host_ok": {
        "en": ("www and non-www are consistent", "{host} redirects to {target}."),
        "bg": ("www и без www са съгласувани", "{host} пренасочва към {target}."),
    },
    "configuration.canonical_host_duplicate": {
        "en": (
            "Both www and non-www serve the site",
            "{host} answers separately instead of redirecting. Search engines see two sites.",
        ),
        "bg": (
            "И www, и без www обслужват сайта",
            "{host} отговаря отделно, вместо да пренасочва. Търсачките виждат два сайта.",
        ),
    },
    "configuration.canonical_host_unreachable": {
        "en": (
            "The www address does not work",
            "{host} did not respond ({error}). Visitors who type it will not reach the site.",
        ),
        "bg": (
            "Адресът с www не работи",
            "{host} не отговори ({error}). Посетители, които го въведат, няма да стигнат до сайта.",
        ),
    },
    "configuration.well_known_blocked": {
        "en": ("{what} could not be checked", "The request was refused (HTTP {status})."),
        "bg": ("{what} не можа да бъде проверен", "Заявката беше отказана (HTTP {status})."),
    },
    "configuration.well_known_unavailable": {
        "en": ("{what} could not be checked", "The request did not complete (HTTP {status})."),
        "bg": ("{what} не можа да бъде проверен", "Заявката не завърши (HTTP {status})."),
    },
    "configuration.robots_present": {
        "en": ("robots.txt is present", "Search engines have crawl instructions."),
        "bg": ("robots.txt е наличен", "Търсачките имат инструкции за обхождане."),
    },
    "configuration.robots_missing": {
        "en": ("robots.txt is missing", "Not a fault, but usually worth adding (HTTP {status})."),
        "bg": (
            "Липсва robots.txt",
            "Не е проблем, но обикновено си струва да се добави (HTTP {status}).",
        ),
    },
    "configuration.sitemap_present": {
        "en": ("Sitemap is present", "Helps search engines find every page."),
        "bg": ("Има карта на сайта", "Помага на търсачките да намерят всяка страница."),
    },
    "configuration.sitemap_missing": {
        "en": ("Sitemap is missing", "Not a fault, but usually worth adding (HTTP {status})."),
        "bg": (
            "Липсва карта на сайта",
            "Не е проблем, но обикновено си струва да се добави (HTTP {status}).",
        ),
    },
    "configuration.favicon_present": {
        "en": ("Favicon is set", "The browser tab icon is configured."),
        "bg": ("Има favicon", "Иконата за таба на браузъра е зададена."),
    },
    "configuration.favicon_missing": {
        "en": ("Favicon is missing", "Minor, but visible in every browser tab (HTTP {status})."),
        "bg": ("Липсва favicon", "Дребно, но се вижда във всеки таб на браузъра (HTTP {status})."),
    },
    # ----------------------------------------------------------------- technology
    "technology.not_checked": {
        "en": ("Technology not checked", "The site did not respond."),
        "bg": ("Технологиите не са проверени", "Сайтът не отговори."),
    },
    "technology.cms_detected": {
        "en": ("Built on {name}", "Detected from the public page source."),
        "bg": ("Изграден на {name}", "Установено от публичния код на страницата."),
    },
    "technology.cms_unknown": {
        "en": ("No common CMS detected", "Either custom-built or well hidden."),
        "bg": ("Не е открита разпространена CMS", "Или е изработен по поръчка, или е добре скрит."),
    },
    "technology.cms_version_exposed": {
        "en": (
            "{name} version is published on the page",
            "The page announces version {version}, which tells everyone which updates are missing.",
        ),
        "bg": (
            "Версията на {name} е публикувана на страницата",
            "Страницата обявява версия {version}, което показва на всички кои обновления липсват.",
        ),
    },
    "technology.ecommerce_detected": {
        "en": ("Online shop detected", "Running {name}."),
        "bg": ("Открит е онлайн магазин", "Използва {name}."),
    },
    "technology.ecommerce_unidentified": {
        "en": ("Online shop detected", "The shop platform could not be identified from the page."),
        "bg": ("Открит е онлайн магазин", "Платформата на магазина не можа да бъде разпозната."),
    },
    "technology.booking_detected": {
        "en": ("Booking or reservation functionality detected", "Worth monitoring separately."),
        "bg": ("Открита е функционалност за резервации", "Струва си да се следи отделно."),
    },
    "technology.server_header": {
        "en": ("Web server identified", "Reports itself as {server}."),
        "bg": ("Разпознат е уеб сървър", "Представя се като {server}."),
    },
    "technology.server_version_exposed": {
        "en": ("Web server version is exposed", "The server announces itself as {server}."),
        "bg": ("Версията на уеб сървъра е видима", "Сървърът се представя като {server}."),
    },
    "technology.powered_by_exposed": {
        "en": ("Backend technology is exposed", "The site announces {value} in its headers."),
        "bg": ("Технологията на бекенда е видима", "Сайтът обявява {value} в своите HTTP Headers."),
    },
    "technology.not_responsive": {
        "en": (
            "No mobile viewport setting",
            "The page has no viewport tag, which usually means it was not built for phones.",
        ),
        "bg": (
            "Няма настройка за мобилен изглед",
            "Страницата няма viewport таг, което обикновено значи, че не е правена за телефони.",
        ),
    },
    "technology.legacy_javascript": {
        "en": (
            "Old JavaScript library in use",
            "{library} {version} is several major versions behind.",
        ),
        "bg": (
            "Използва се стара JavaScript библиотека",
            "{library} {version} изостава с няколко основни версии.",
        ),
    },
    # ---------------------------------------------------------------- performance
    "performance.not_checked": {
        "en": ("Performance not checked", "The site did not respond."),
        "bg": ("Производителността не е проверена", "Сайтът не отговори."),
    },
    "performance.response_fast": {
        "en": ("Server responds quickly", "First response in {duration}."),
        "bg": ("Сървърът отговаря бързо", "Първи отговор за {duration}."),
    },
    "performance.response_slow": {
        "en": ("Server is slow to respond", "First response took {duration}."),
        "bg": ("Сървърът отговаря бавно", "Първият отговор отне {duration}."),
    },
    "performance.response_very_slow": {
        "en": (
            "Server is very slow to respond",
            "First response took {duration}, before any images or scripts load.",
        ),
        "bg": (
            "Сървърът отговаря много бавно",
            "Първият отговор отне {duration}, преди да се заредят изображения и скриптове.",
        ),
    },
    "performance.document_size_ok": {
        "en": ("Homepage document is a reasonable size", "{kb} KB of HTML."),
        "bg": ("Документът на началната страница е с разумен размер", "{kb} KB HTML."),
    },
    "performance.document_large": {
        "en": ("Homepage document is large", "{kb} KB of HTML before images and scripts."),
        "bg": (
            "Документът на началната страница е голям",
            "{kb} KB HTML преди изображения и скриптове.",
        ),
    },
    "performance.compression_ok": {
        "en": ("Compression is enabled", "Served with {encoding}."),
        "bg": ("Компресията е включена", "Обслужва се с {encoding}."),
    },
    "performance.compression_missing": {
        "en": (
            "Compression is not enabled",
            "The homepage is sent uncompressed, which makes it slower than it needs to be.",
        ),
        "bg": (
            "Компресията не е включена",
            "Началната страница се изпраща некомпресирана, което я забавя без нужда.",
        ),
    },
}

PROSPECT_SIGNALS = {
    "en": {
        "wordpress": "Runs WordPress",
        "woocommerce": "Runs WooCommerce",
        "slow_response": "Slow to respond",
        "missing_headers": "Missing security headers",
        "outdated_site": "Site looks dated",
        "business_form": "Business-critical form",
        "booking_ecommerce": "Booking or online sales",
        "local_bg_sme": "Local Bulgarian business",
    },
    "bg": {
        "wordpress": "Работи на WordPress",
        "woocommerce": "Работи на WooCommerce",
        "slow_response": "Бавен отговор",
        "missing_headers": "Липсващи HTTP Headers за сигурност",
        "outdated_site": "Сайтът изглежда остарял",
        "business_form": "Форма, важна за бизнеса",
        "booking_ecommerce": "Резервации или онлайн продажби",
        "local_bg_sme": "Местен български бизнес",
    },
}


def resolve(finding: Finding, lang: str = DEFAULT_LANGUAGE) -> tuple[str, str]:
    """Return (title, detail) for a finding, falling back gracefully.

    An unknown id renders as the id itself rather than raising: a report with one
    ugly line is recoverable, a scan that crashes on a new check is not.
    """
    entry = MESSAGES.get(finding.id)
    if entry is None:
        # External engines supply their own wording. It is English only, which is
        # a known gap: the Bulgarian report falls back to it rather than lying.
        if finding.title:
            return finding.title, finding.detail or ""
        return finding.id, ""
    title_template, detail_template = entry.get(lang) or entry[DEFAULT_LANGUAGE]
    return _format(title_template, finding.params), _format(detail_template, finding.params)


def _format(template: str, params: dict) -> str:
    try:
        return template.format(**params)
    except (KeyError, IndexError, ValueError):
        return template


def heading(key: str, lang: str = DEFAULT_LANGUAGE) -> str:
    return HEADINGS.get(lang, HEADINGS[DEFAULT_LANGUAGE]).get(key, key)


def signal_name(key: str, lang: str = DEFAULT_LANGUAGE) -> str:
    return PROSPECT_SIGNALS.get(lang, PROSPECT_SIGNALS[DEFAULT_LANGUAGE]).get(key, key)


def category_name(key: str, lang: str = DEFAULT_LANGUAGE) -> str:
    return CATEGORY_NAMES.get(lang, CATEGORY_NAMES[DEFAULT_LANGUAGE]).get(key, key)
