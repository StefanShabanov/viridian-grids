"""Turn a raw scan into the customer-facing report the website renders.

The website's report page (`apps/web/src/scripts/report.ts`) expects a curated
`Report` object - a verdict, what it means for the business, the one urgent
thing, then CVEs and the rest - not the raw finding list. This module is the
bridge: it reads a `ScanResult` and produces that object, in Bulgarian, for
every prospect automatically, so a cold-outreach report reads like the one we
hand-wrote for the first client instead of a bare score.

Everything here is derived from the scan and the local intel cache - no network,
no per-site authoring. Where the scan carries English engine prose (webanalyze,
Observatory, the intel CVE/EOL findings), we rebuild the Bulgarian ourselves;
only our own checks are pulled through the catalog, which already speaks Bulgarian.

The wording is customer-facing Bulgarian and still owes a native review before a
first send, same as the rest of the outreach copy.
"""

from __future__ import annotations

from .catalog import BANDS, DISCLAIMER, resolve
from .intel.store import IntelStore
from .models import Finding, ScanResult, Status
from .scoring import band

BAND_TONE = {"good": "good", "fair": "fair", "poor": "bad"}
_SEV_RANK = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


def _clean_business(name: str | None) -> str | None:
    """Calm the harvest's ALL-CAPS company names without touching real casing.

    OSM data yells ("ЛИВАДИТЕ") or leaves brands mixed ("DENTestetica", "Paloma").
    Only words that are entirely upper-case are title-cased; anything with a
    lower-case letter is left exactly as the owner writes it. This cannot fix a
    truncated or wrong name - those are flagged for a human, not guessed here.
    """
    if not name or not name.strip():
        return None
    words = name.strip().split()
    fixed = [w if any(c.islower() for c in w) else w.capitalize() for w in words]
    return " ".join(fixed)


# The one CVE caveat that keeps the report honest: a version-matched CVE is not
# proof of a breach, because hosts backport fixes without bumping the version.
CVE_CAVEAT = (
    "Наличието на докладвана уязвимост срещу дадена версия не значи автоматично, "
    "че сайтът е пробит - някои хостинг доставчици връщат поправките назад, без да "
    "сменят номера на версията. Затова първата стъпка е да се потвърди с хостинга, "
    "а не да се приема най-лошото."
)


def _cve_what(summary: str) -> str:
    """A plain-Bulgarian one-liner for a CVE, classified from its NVD summary.

    Not a translation - a category. The exact mechanics live one click away on
    NVD; here we only tell a non-technical owner what kind of problem it is.
    """
    s = summary.lower()
    if any(k in s for k in ("arbitrary code", "code execution", "remote code")):
        return "При определени условия може да позволи изпълнение на чужд код на сървъра."
    if "sql injection" in s:
        return "Може да позволи достъп до базата данни чрез SQL инжекция."
    if "cross-site scripting" in s or " xss" in s:
        return "Може да позволи вкарване на зловреден скрипт в страницата (XSS)."
    if any(
        k in s
        for k in (
            "buffer",
            "out-of-bounds",
            "memory corruption",
            "use-after-free",
            "heap",
            "stack consumption",
            "overflow",
        )
    ):
        return "Проблем с паметта, който може да срине приложението или да доведе до неочаквано поведение."
    if any(k in s for k in ("denial of service", "crash", "infinite loop", "resource")):
        return "Може да натовари или срине сайта (отказ на услуга)."
    if any(
        k in s for k in ("bypass", "authentication", "authorization", "access control", "privilege")
    ):
        return "Може да позволи заобикаляне на защита или повишаване на права."
    if any(k in s for k in ("traversal", "arbitrary file", "read file", "include")):
        return "Може да позволи достъп до файлове извън предвидените."
    if any(k in s for k in ("disclosure", "leak", "expose", "sensitive")):
        return "Може да разкрие данни, които не би трябвало да са публични."
    if "request forgery" in s or "csrf" in s:
        return "Може да подмами вписан потребител да извърши нежелано действие (CSRF)."
    if "open redirect" in s:
        return "Може да пренасочи посетител към чужд адрес."
    return "Докладвана уязвимост в тази версия; подробностите са в NVD."


def _eol_findings(result: ScanResult) -> list[Finding]:
    return [f for f in result.findings if f.id.startswith("intel.eol")]


def _has_broken_tls(result: ScanResult) -> Finding | None:
    for f in result.findings:
        if f.status is Status.FAIL and f.id in (
            "tls.hostname_mismatch",
            "tls.certificate_untrusted",
        ):
            return f
    return None


def _server_hint(result: ScanResult) -> str:
    """A hosting-specific nudge for the urgent note, when we can tell the server."""
    tech = " ".join(
        f"{f.params.get('name', '')}".lower()
        for f in result.findings
        if f.id.startswith(("webanalyze.version", "webanalyze.server", "technology."))
    )
    if "litespeed" in tech:
        return (
            "Сървърът изглежда LiteSpeed, което обикновено значи cPanel или CloudLinux. "
            "Тези платформи често предлагат PHP с върнати назад поправки - тоест номерът на "
            "версията си остава същият, но уязвимостите са отстранени. Първо това си струва да се провери с хостинга."
        )
    if "nginx" in tech or "apache" in tech:
        return (
            "Струва си да попитате хостинг доставчика дали може да Ви качи на поддържана версия - "
            "често е смяна на панел или на PHP от контролния панел, не пренаписване на сайта."
        )
    return ""


def _cve_groups(result: ScanResult, store: IntelStore) -> list[dict]:
    groups: list[dict] = []
    for f in result.findings:
        if not f.id.startswith("intel.cve"):
            continue
        product = str(f.params.get("name", ""))
        version = str(f.params.get("version", ""))
        payload = store.get("cve", product, version, allow_stale=True) or []
        items = sorted(payload, key=lambda c: _SEV_RANK.get(str(c.get("severity", "")).upper(), 4))
        if not items:
            # Fall back to the ids the scan already carries, worst-severity unknown.
            items = [
                {"cve": cid, "severity": str(f.params.get("worst", "MEDIUM")), "summary": ""}
                for cid in f.evidence.get("cves", [])
            ]
        reported = len(items)
        shown = items[:6]
        crit = sum(1 for c in items if str(c.get("severity", "")).upper() == "CRITICAL")
        high = sum(1 for c in items if str(c.get("severity", "")).upper() == "HIGH")
        eol = next(
            (e for e in _eol_findings(result) if str(e.params.get("name", "")) == product), None
        )
        if eol:
            note = (
                f"Показани са {len(shown)}-те най-сериозни от {reported} докладвани. "
                f"{product} {eol.params.get('cycle', version)} вече не получава поправки от "
                "разработчиците му, така че този списък няма да намалява от само себе си."
            )
        else:
            note = (
                f"Показани са {len(shown)}-те най-сериозни от {reported} докладвани за тази версия."
            )
        groups.append(
            {
                "product": product,
                "version": version,
                "reported": reported,
                "shown": len(shown),
                "critical": crit,
                "high": high,
                "note": note,
                "items": [
                    {
                        "id": str(c.get("cve", "")),
                        "severity": str(c.get("severity", "MEDIUM")).upper(),
                        "what": _cve_what(str(c.get("summary", ""))),
                    }
                    for c in shown
                ],
            }
        )
    groups.sort(key=lambda g: (-g["critical"], -g["high"], -g["reported"]))
    return groups


def _detected(result: ScanResult) -> list[str]:
    seen: list[str] = []
    for f in result.findings:
        if f.id.startswith("webanalyze.version") or f.id in (
            "webanalyze.cms",
            "technology.cms_detected",
        ):
            name = str(f.params.get("name", "")).strip()
            version = str(f.params.get("version", "")).strip()
            label = f"{name} {version}".strip()
            if name and label not in seen:
                seen.append(label)
    return seen


def _urgent(result: ScanResult) -> dict | None:
    broken = _has_broken_tls(result)
    if broken:
        return {
            "label": "Най-важното",
            "title": "HTTPS сертификатът на сайта не е валиден",
            "detail": (
                "Посетител, който отвори сайта през HTTPS, вижда предупреждение за сигурност вместо "
                "страницата Ви. Това е първото нещо, което бихме поправили - и обикновено е смяна на "
                "сертификата от хостинга, не преработка на сайта."
            ),
            "note": _server_hint(result),
        }
    eols = _eol_findings(result)
    if eols:
        # The oldest end-of-life line is the most defensible thing to lead with.
        worst = eols[0]
        name = str(worst.params.get("name", ""))
        cycle = str(worst.params.get("cycle", ""))
        return {
            "label": "Най-важното",
            "title": f"{name} {cycle} - без обновявания за сигурност",
            "detail": (
                "Това е единственото нещо в отчета, което наистина има срок. Софтуерът, на който върви "
                "сайтът, вече не получава поправки от разработчиците му, така че новите пропуски остават "
                "отворени. Всичко останало по-долу са настройки, които се оправят бързо."
            ),
            "note": _server_hint(result),
        }
    if _has_cve(result):
        return {
            "label": "Най-важното",
            "title": "Публично известни уязвимости в използвания софтуер",
            "detail": (
                "Срещу версиите, които сайтът използва, има публично докладвани уязвимости. Не е знак, "
                "че сайтът е пробит, но е причина да се обнови - подробностите и препоръката са по-долу."
            ),
            "note": _server_hint(result),
        }
    return None


def _has_cve(result: ScanResult) -> bool:
    return any(f.id.startswith("intel.cve") for f in result.findings)


def _summary(result: ScanResult) -> list[dict]:
    fast = not any(
        f.id.startswith("performance.response")
        for f in result.findings
        if f.status in (Status.WARN, Status.FAIL)
    )
    eol_names = sorted({str(f.params.get("name", "")) for f in _eol_findings(result)})
    cards = [
        {
            "title": "Сайтът работи",
            "text": (
                "Проверката установи, че сайтът отговаря и се зарежда"
                + (" бързо." if fast else ", макар и по-бавно от желаното.")
            ),
        }
    ]
    if eol_names:
        cards.append(
            {
                "title": "Софтуерът отдолу е остарял",
                "text": "Част от софтуера ({}) вече не се поддържа с обновявания за сигурност от разработчиците му.".format(
                    ", ".join(eol_names)
                ),
            }
        )
    cards.append(
        {
            "title": "Какво означава това",
            "text": (
                "Не е спешен пробив, а натрупващ се риск: колкото по-дълго стои остаряло, толкова повече "
                "известни пропуски се събират. Оправя се с поддръжка, не с паника."
            ),
        }
    )
    return cards[:3]


def _tech_words(result: ScanResult) -> str:
    return " ".join(
        f"{f.params.get('name', '')}".lower()
        for f in result.findings
        if f.id.startswith(("webanalyze", "technology."))
    )


def _join_bg(items: list[str]) -> str:
    items = [i for i in items if i]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} и {items[1]}"
    return ", ".join(items[:-1]) + " и " + items[-1]


# What the worst vulnerability on this site actually lets happen, in plain words.
# Keyed off the classified `what` line so it follows the real CVE, not a guess.
def _consequence(what: str, is_wp: bool) -> str:
    w = what.lower()
    if "изпълнение на чужд код" in w:
        if is_wp:
            return (
                "При такава уязвимост сайтове на WordPress най-често биват подменени с чужда страница или "
                "пренасочени към спам - без да е нужна паролата Ви."
            )
        return "Тя позволява при определени условия чужд код да се изпълни на сървъра - най-тежкото за един сайт."
    if "sql" in w:
        return "Тя засяга базата от данни зад формите на сайта - там, където се пазят запитванията и контактите."
    if "скрипт" in w:
        return "Тя позволява вкарване на чужд скрипт в страниците, които виждат посетителите Ви."
    if "паметта" in w or "отказ на услуга" in w or "срине" in w:
        return "Тя може да срине сайта или да го направи нестабилен в неподходящ момент."
    if "разкрие данни" in w:
        return "Тя може да разкрие данни, които не би трябвало да са публични."
    if "файлове" in w:
        return "Тя може да отвори достъп до файлове на сървъра извън предвидените."
    if "заобикаляне" in w or "права" in w:
        return "Тя може да позволи заобикаляне на защитата или повишаване на права в системата."
    return "Поправка за нея вече съществува - сайтът просто още не я е приложил."


def _catcher(result: ScanResult, cve_groups: list[dict]) -> str:
    """The hook: one honest, concrete opening built from THIS site's own findings -
    the exact software and versions, the count of known vulnerabilities, the single
    worst CVE by id, and what it actually lets happen. Because those vary per site,
    so does the catcher. Not alarmism: a version-matched CVE is not proof of a
    breach (the caveat under the CVE list says so), but it is a real, specific risk.
    """
    if _has_broken_tls(result):
        return (
            "Точно сега всеки, който отвори сайта Ви, среща предупреждение „Връзката не е сигурна“ на "
            "цял екран вместо началната страница. Повечето хора си тръгват още там - преди да видят "
            "каквото и да било от Вас."
        )

    is_wp = "wordpress" in _tech_words(result)

    if cve_groups:
        names = [f"{g['product']} {g['version']}".strip() for g in cve_groups if g["product"]]
        if len(names) > 3:
            names = names[:2] + ["и др."]
        software = _join_bg(names)
        verb = "има" if len([n for n in names if n != "и др."]) == 1 else "имат"
        total = sum(g["reported"] for g in cve_groups)
        crit = sum(g["critical"] for g in cve_groups)
        high = sum(g["high"] for g in cve_groups)
        worst = cve_groups[0]["items"][0] if cve_groups[0]["items"] else None
        if crit:
            count_clause = f" ({crit} критична)" if crit == 1 else f" ({crit} критични)"
        elif high:
            count_clause = f" ({high} висока)" if high == 1 else f" ({high} високи)"
        else:
            count_clause = ""
        noun = "известна уязвимост" if total == 1 else "известни уязвимости"
        if worst and worst.get("id"):
            lead = (
                f"{software} {verb} {total} {noun}{count_clause}, "
                f"най-тежката от които е {worst['id']}. "
            )
            return lead + _consequence(worst.get("what", ""), is_wp)
        return (
            f"{software} {verb} {total} {noun}{count_clause}, срещу които вече има издадени поправки - "
            "сайтът просто още не ги е приложил."
        )

    if _eol_findings(result):
        worst = _eol_findings(result)[0]
        name = f"{worst.params.get('name', '')} {worst.params.get('cycle', '')}".strip()
        return (
            f"{name} вече не получава обновявания за сигурност. Въпросът не е дали ще се появи нова "
            "уязвимост, а кога - и тя ще остане отворена, защото няма кой да я поправи."
        )
    return (
        "Няма спешен проблем. Има няколко неща по сигурността и поддръжката, които се трупат тихо и се "
        "оправят по-лесно сега, отколкото по-късно."
    )


def _attention(result: ScanResult, urgent: Finding | None, lang: str) -> list[dict]:
    out: list[dict] = []
    for f in result.by_status(Status.FAIL, Status.WARN):
        if f.source != "vg":  # engine prose is English; keep those out of the Bulgarian body
            continue
        if urgent is not None and f.id == urgent.id:
            continue
        title, detail = resolve(f, lang)
        if not title:
            continue
        item = {"title": title}
        if detail:
            item["detail"] = detail
        out.append(item)
    return out[:8]


def _working(result: ScanResult, lang: str) -> list[str]:
    out: list[str] = []
    for f in result.by_status(Status.PASS):
        if f.source != "vg":
            continue
        title, _ = resolve(f, lang)
        if title:
            out.append(title)
    return out[:8]


def _next_steps(result: ScanResult) -> list[dict]:
    steps: list[dict] = []
    n = 1
    if _has_broken_tls(result):
        steps.append(
            {
                "step": str(n),
                "title": "Валиден HTTPS сертификат",
                "effort": "≈ 1 час",
                "text": "Издаване и монтиране на правилен сертификат, за да изчезне предупреждението при отваряне на сайта.",
            }
        )
        n += 1
    if _eol_findings(result):
        steps.append(
            {
                "step": str(n),
                "title": "Обновяване на остарелия софтуер",
                "effort": "координация с хостинга",
                "text": "Качване на поддържана версия на сървърния софтуер и системата за управление, с проверка, че сайтът работи след това.",
            }
        )
        n += 1
    steps.append(
        {
            "step": str(n),
            "title": "Заглавки и бисквитки за сигурност",
            "effort": "≈ 1 час",
            "text": "Добавяне на липсващите заглавки (HSTS, CSP и др.) и на флаговете за бисквитките - бърза, но осезаема стъпка.",
        }
    )
    n += 1
    steps.append(
        {
            "step": str(n),
            "title": "Наблюдение и поддръжка",
            "effort": "текущо",
            "text": "Наблюдение на достъпността и сертификата, редовни обновявания и архиви - за да не се стига пак дотук.",
        }
    )
    return steps


def build_report(
    result: ScanResult,
    lang: str = "bg",
    *,
    business: str | None = None,
    date: str | None = None,
    store: IntelStore | None = None,
) -> dict:
    """Assemble the website's `Report` object from a scan. Bulgarian by default."""
    store = store or IntelStore()
    band_key = band(result.score)
    urgent_finding = _has_broken_tls(result) or (
        _eol_findings(result)[0] if _eol_findings(result) else None
    )
    when = date or result.scanned_at.strftime("%d.%m.%Y")
    cve_groups = _cve_groups(result, store)

    report = {
        "domain": result.domain,
        "score": result.score,
        "scoreMax": 100,
        "band": BANDS.get(lang, BANDS["bg"])[band_key],
        "bandTone": BAND_TONE[band_key],
        "date": when,
        "headline": _catcher(result, cve_groups),
        "summary": _summary(result),
        "cveCaveat": CVE_CAVEAT,
        "cveGroups": cve_groups,
        "attention": _attention(result, urgent_finding, lang),
        "working": _working(result, lang),
        "detected": _detected(result),
        "next": _next_steps(result),
        "checks": {
            "label": "Какво включва тази проверка",
            "note": (
                "Публична, неинвазивна проверка на здравето на сайта: достъпност, HTTPS сертификат, "
                "заглавки за сигурност, бисквитки, разпознаване на технологии по версии и справка с "
                "публични бази за край на поддръжката и известни уязвимости. Никакви атаки, паролни опити или "
                "агресивно обхождане."
            ),
            "engines": "Ползвани източници: webanalyze, Mozilla Observatory, endoflife.date и NVD/NIST.",
        },
        "disclaimer": DISCLAIMER.get(lang, DISCLAIMER["bg"]),
        "prepared": f"Изготвено от Viridian Grids · {when}",
    }
    cleaned = _clean_business(business)
    if cleaned:
        report["business"] = cleaned
    urgent = _urgent(result)
    if urgent:
        report["urgent"] = urgent
    return report
