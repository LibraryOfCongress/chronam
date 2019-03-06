from django.db.models import Max
from django.contrib.syndication.views import Feed
from django.core.urlresolvers import reverse
from django.utils.feedgenerator import Atom1Feed

from chronam.core.models import Title


class NewspaperFeedAtom(Feed):
    title = "Recent Titles from Chronicling America"
    subtitle = (
        "This feed lists newspaper titles that have had new content added to them."
    )
    feed_type = Atom1Feed
    link = "/newspapers/"
    feed_guid = "info:lc/ndnp/newspapers"
    author_name = "Library of Congress"
    author_link = "https://www.loc.gov"

    def items(self):
        return (
            Title.objects.filter(has_issues=True, issues__batch__released__isnull=False)
            .annotate(last_release=Max("issues__batch__released"))
            .order_by("-last_release")
        )

    def item_link(self, item):
        return reverse("chronam_title", args=[item.lccn])

    def item_updateddate(self, item):
        return item.issues.order_by("-batch__released").first().batch.released

    def item_author_name(self, item):
        return item.publisher

    def item_description(self, item):
        updated = item.issues.first().batch.released.strftime("%Y-%m-%d")
        return "Issues were added on %s for %s" % (updated, item.name)

    def item_title(self, item):
        return "Updated content for %s (%s)" % (item.name, item.place_of_publication)
