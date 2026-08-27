"""Turning volunteer-typed website tags into a host the scanner can take."""

from __future__ import annotations

import pytest

from vg_harvest.normalize import is_shared_host, is_social, registrable, to_domain


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("https://dentalargirova.com/", "dentalargirova.com"),
        ("http://avend.bg/", "avend.bg"),
        ("www.smilefactorybg.com", "smilefactorybg.com"),
        ("HTTPS://WWW.Example.BG/za-nas?utm_source=osm", "example.bg"),
        ("  https://example.bg  ", "example.bg"),
    ],
)
def test_website_tags_become_scannable_hosts(raw, expected):
    assert to_domain(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("https://shop.example.bg", "shop.example.bg"),
        ("https://example.com.bg", "example.com.bg"),
    ],
)
def test_subdomains_are_kept_because_they_are_the_actual_site(raw, expected):
    """Collapsing to the registrable domain would scan a different website. The
    Public Suffix List has no com.bg entry, so example.com.bg would have collapsed
    to com.bg, which belongs to someone else."""
    assert to_domain(raw) == expected


def test_registrable_domain_is_still_available_for_classification():
    assert registrable("https://shop.example.bg") == "example.bg"
    assert registrable("https://kornelia-petkova.add.bg") == "add.bg"


@pytest.mark.parametrize(
    "raw",
    [
        "https://www.facebook.com/dentalclinic",
        "https://instagram.com/somedentist",
        "https://superdoc.bg/lekar/antonin-x",
        "https://www.booking.com/hotel/bg/x.html",
    ],
)
def test_social_and_directory_pages_are_not_websites(raw):
    """We cannot monitor, update or back up somebody else's Facebook page, and
    selling maintenance for one would be dishonest."""
    assert is_social(raw)
    assert to_domain(raw) is None


@pytest.mark.parametrize("raw", ["", "   ", "not a url", "mailto:x@y.bg", "tel:+35921234", "bg"])
def test_rubbish_tags_are_rejected(raw):
    assert to_domain(raw) is None


def test_builder_subdomains_are_recognised():
    """kornelia-petkova.add.bg is a template on a hosting provider."""
    assert is_shared_host("http://kornelia-petkova.add.bg/")
    assert is_shared_host("https://someclinic.wixsite.com/home")


def test_a_real_business_subdomain_is_not_treated_as_hosted():
    """Flagging every subdomain would throw away genuine prospects."""
    assert not is_shared_host("https://shop.example.bg")
    assert not is_shared_host("https://www.example.bg/")
