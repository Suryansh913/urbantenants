from django.contrib.sitemaps import Sitemap
from django.urls import reverse

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