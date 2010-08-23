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
        countries = set()
        for title in models.Title.objects.distinct().filter(issues__isnull=False):
            title_name = "%s (%s)" % (title.name, title.place_of_publication)
            titles.append((title.lccn, title_name))
            countries.add(title.country)

        states = [("", "All states")]

        # TODO: candidate for memcache or some such?
        years = [("", "All")]

        dates = list(models.Issue.objects.dates('date_issued', 'year'))
        MIN_YEAR = 1860
        MAX_YEAR = 1922
        if len(dates)==0:
            fulltextStartYear = MIN_YEAR
            fulltextEndYear = MAX_YEAR
        else:
            fulltextStartYear = dates[0].year
            fulltextEndYear = dates[-1].year

            # See: https://rdc.lctl.gov/trac/ndnp/ticket/446
            fulltextStartYear = max(fulltextStartYear, MIN_YEAR) 

            # I don't understand why... just doing what's asked. See:
            # https://rdc.lctl.gov/trac/ndnp/ticket/241
            fulltextEndYear = min(fulltextEndYear, MAX_YEAR) 
            years.extend((year, year) for year in range(fulltextStartYear, fulltextEndYear+1))
        self.fulltextStartYear = fulltextStartYear
        self.fulltextEndYear = fulltextEndYear

        for country in countries:
            states.append((country.name, country.name))
        states = sorted(states)

        self.fields["lccn"].choices = titles
        self.fields["state"].choices = states
        self.fields["year"].choices = years
