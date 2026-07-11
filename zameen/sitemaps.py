from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from listings.models import listings


class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        return [
            'base',
            'bhk2',
            'bhk3',
            'pg',
            'aboutus',
            'Terms-condition',
            'privacy-policy',
            'more',
        ]

    def location(self, item):
        return reverse(item)


class ListingSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        # Only include rooms that are actually available/active,
        # so Google doesn't index dead/booked listings.
        return listings.objects.filter(Room_available=True)

    def lastmod(self, obj):
        return obj.date

    def location(self, obj):
        return reverse('room', args=[obj.id])