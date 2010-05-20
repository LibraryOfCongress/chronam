from django import forms
from django.forms import fields

from chronam.web import models


class SearchPagesForm(forms.Form):
    lccn = fields.MultipleChoiceField(choices=[], initial="")
    lccn.widget.attrs['size'] = 8

    state = fields.MultipleChoiceField(choices=[], initial="") 
    state.widget.attrs['size'] = 8

    year = fields.ChoiceField(choices=[])

    date1 = fields.DateTimeField()
    date2 = fields.DateTimeField()

    ortext = fields.CharField()
    andtext = fields.CharField() 
    phrasetext = fields.CharField()
    proxtext = fields.CharField()
    proxdistance = fields.ChoiceField(choices=[("5", "5"), 
                                               ("10", "10"),
                                               ("50", "50"),
                                               ("100", "100")], initial="5")

    def __init__(self, *args, **kwargs):
        super(forms.Form, self).__init__(*args, **kwargs)
        
        titles = [("", "All newspapers")]
        for title in models.Title.objects.distinct().filter(issues__isnull=False):
            title_name = "%s (%s)" % (title.name, title.place_of_publication)
            titles.append((title.lccn, title_name))

        states = [("", "All states")]

        # TODO: candidate for memcache or some such?
        years = [("", "All")]

        dates = list(models.Issue.objects.dates('date_issued', 'year'))
        if len(dates)==0:
            fulltextStartYear = 1880
            fulltextEndYear = 1922
        else:
            fulltextStartYear = dates[0].year
            fulltextEndYear = dates[-1].year

            # See: https://rdc.lctl.gov/trac/ndnp/ticket/446
            fulltextStartYear = max(fulltextStartYear, 1880) 

            # I don't understand why... just doing what's asked. See:
            # https://rdc.lctl.gov/trac/ndnp/ticket/241
            fulltextEndYear = min(fulltextEndYear, 1922) 
            years.extend((year, year) for year in range(fulltextStartYear, fulltextEndYear+1))
        self.fulltextStartYear = fulltextStartYear
        self.fulltextEndYear = fulltextEndYear

        # TODO: remove hard-coded list
        states.extend([
                ("Arizona", "AZ"),
                ("California", "CA"),
                ("District of Columbia", "DC"),
                ("Florida", "FL"),
                ("Hawaii", "HI"),
                ("Kentucky", "KY"),
                ("Minnesota", "MN"),
                ("Missouri", "MO"),
                ("Nebraska", "NE"),
                ("New York", "NY"),
                ("Ohio", "OH"),
                ("Pennsylvania", "PA"),
                ("Texas", "TX"),
                ("Utah", "UT"),
                ("Virginia", "VA"),
                ("Washington", "WA")])

        self.fields["lccn"].choices = titles
        self.fields["state"].choices = states
        self.fields["year"].choices = years
