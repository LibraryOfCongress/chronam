from django.contrib import sitemaps

from chronam.core.models import Batch, Issue, Page, Title


class BatchesSitemap(sitemaps.Sitemap):
    changefreq = "daily"

    def items(self):
        return Batch.objects.all()

    def lastmod(self, batch):
        return batch.released

    def location(self, batch):
        return batch.url


class IssuesSitemap(sitemaps.Sitemap):
    changefreq = "daily"

    def items(self):
        return Issue.objects.prefetch_related("title")

    def lastmod(self, issue):
        return issue.created

    def location(self, issue):
        return issue.url


class PagesSitemap(sitemaps.Sitemap):
    changefreq = "daily"
    # Reduce the number of pages from the default 50,0000 to reduce the size of
    # some of the database queries:
    limit = 10000

    def items(self):
        return Page.objects.order_by("pk").prefetch_related("issue", "issue__title")

    def lastmod(self, page):
        return page.created

    def location(self, page):
        return page.url


class TitlesSitemap(sitemaps.Sitemap):
    changefreq = "daily"

    def items(self):
        return Title.objects.filter(has_issues=True)

    def lastmod(self, title):
        return title.created

    def location(self, title):
        return title.url
