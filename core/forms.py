import datetime

from django import forms
from django.forms import fields
from django.conf import settings
from django.core.cache import cache
from django.db.models import Min, Max

from chronam.core import models

MIN_YEAR = 1860
MAX_YEAR = 1922
DAY_CHOICES = [(i, i) for i in range(1,32)]
MONTH_CHOICES = ((1, u'Jan',), (2, u'Feb',), (3, u'Mar',),
                 (4, u'Apr',), (5, u'May',), (6, u'Jun',),
                 (7, u'Jul',), (8, u'Aug',), (9, u'Sep',),
                 (10, u'Oct',), (11, u'Nov',), (12, u'Dec',)) 

FREQUENCY_CHOICES = (
    ("", "Select"),
    ("Daily", "Daily"),
    ("Three times a week", "Three times a week"),
    ("Semiweekly", "Semiweekly"),
    ("Weekly", "Weekly"),
    ("Biweekly", "Biweekly"),
    ("Three times a month", "Three times a month"),
    ("Semimonthly", "Semimonthly"),
    ("Monthly", "Monthly"),
    ("Other", "Other"),
    ("Unknown", "Unknown"),
)

PROX_CHOICES = (
    ("5", "5"),
    ("10", "10"),
    ("50", "50"),
    ("100", "100"),
)


def _titles_states():
    """
    returns a tuple of two elements (list of titles, list of states)

    example return value:
    ([('', 'All newspapers'), (u'sn83030214', u'New-York tribune. (New York [N.Y.])')], 
     [('', 'All states'), (u'New York', u'New York')])
    """
    titles_states = cache.get("titles_states")
    if not titles_states:
        titles = [("", "All newspapers"), ]
        states = [("", "All states")]
        # create a temp Set _states to hold states before compiling full list
        _states = set()
        for title in models.Title.objects.filter(has_issues=True).select_related():
            short_name = title.name.split(":")[0]  # remove subtitle
            title_name = "%s (%s)" % (short_name,
                                      title.place_of_publication)
            titles.append((title.lccn, title_name))
            for p in title.places.all():
                _states.add(p.state)
        _states = filter(lambda s: s is not None, _states)
        for state in _states:
            states.append((state, state))
        states = sorted(states)
        cache.set("titles_states", (titles, states))
    else:
        titles, states = titles_states
    return (titles, states)


def _fulltext_range():
    fulltext_range = cache.get('fulltext_range')
    if not fulltext_range:
        # get the maximum and minimum years that we have content for
        issue_dates = models.Issue.objects.all().aggregate(min_date=Min('date_issued'),
                                                           max_date=Max('date_issued'))

        # when there is no content these may not be set
        if issue_dates['min_date']:
            min_year = issue_dates['min_date'].year
        else:
            min_year = MIN_YEAR
        if issue_dates['max_date']:
            max_year = issue_dates['max_date'].year
        else:
            max_year = MAX_YEAR

        # removing these bits for https://rdc.lctl.gov/trac/chronam/ticket/1025
        # See: https://rdc.lctl.gov/trac/ndnp/ticket/446
        #min_year = max(min_year, MIN_YEAR)

        # I don't understand why... just doing what's asked. See:
        # https://rdc.lctl.gov/trac/ndnp/ticket/241
        #max_year = min(max_year, MAX_YEAR)

        fulltext_range = (min_year, max_year)
        cache.set('fulltext_range', fulltext_range)
    return fulltext_range


class SearchPagesForm(forms.Form):
    state = fields.ChoiceField(choices=[])
    date1 = fields.ChoiceField(choices=[])
    date2 = fields.ChoiceField(choices=[])
    proxtext = fields.CharField()
    sequence = fields.BooleanField()
    issue_date = fields.BooleanField()

    def __init__(self, *args, **kwargs):
        super(SearchPagesForm, self).__init__(*args, **kwargs)

        self.titles, self.states = _titles_states()

        fulltextStartYear, fulltextEndYear = _fulltext_range()

        self.years = [(year, year) for year in range(fulltextStartYear, fulltextEndYear + 1)]
        self.fulltextStartYear = fulltextStartYear
        self.fulltextEndYear = fulltextEndYear

        self.fields["state"].choices = self.states
        self.fields["date1"].choices = self.years
        self.fields["date1"].initial = fulltextStartYear
        self.fields["date2"].choices = self.years
        self.fields["date2"].initial = fulltextEndYear
        self.fields["sequence"].widget.attrs['value'] = 1


class AdvSearchPagesForm(SearchPagesForm):
    date_month = fields.ChoiceField(choices=MONTH_CHOICES)
    date_day = fields.ChoiceField(choices=DAY_CHOICES)
    lccn = fields.MultipleChoiceField(choices=[])
    state = fields.MultipleChoiceField(choices=[])
    date1 = fields.CharField()
    date2 = fields.CharField()
    sequence = fields.CharField()
    ortext = fields.CharField()
    andtext = fields.CharField()
    phrasetext = fields.CharField()
    proxtext = fields.CharField()
    proxdistance = fields.ChoiceField(choices=PROX_CHOICES)
    language = fields.ChoiceField()

    def __init__(self, *args, **kwargs):
        super(AdvSearchPagesForm, self).__init__(*args, **kwargs)

        self.date = self.data.get('date1', '')

        self.fields["lccn"].widget.attrs = {'id': 'id_lccns', 'size': '8'}
        self.fields["lccn"].choices = self.titles
        self.fields["state"].widget.attrs = {'id': 'id_states', 'size': '8'}
        self.fields["date1"].widget.attrs = {"id": "id_date_from", "max_length": 10}
        self.fields["date1"].initial = ""
        self.fields["date2"].widget.attrs = {"id": "id_date_to", "max_length": 10}
        self.fields["date2"].initial = ""
        self.fields["sequence"].widget.attrs = {"id": "id_char_sequence", "size": "3"}
        self.fields["proxtext"].widget.attrs["id"] = "id_proxtext_adv"
        lang_choices = [("", "All"), ]
        lang_choices.extend((l, models.Language.objects.get(code=l).name) for l in settings.SOLR_LANGUAGES)
        self.fields["language"].choices = lang_choices


class SearchTitlesForm(forms.Form):
    state = fields.ChoiceField(choices=[], initial="")
    county = fields.ChoiceField(choices=[], initial="")
    city = fields.ChoiceField(choices=[], initial="")
    year1 = fields.ChoiceField(choices=[], label="from")
    year2 = fields.ChoiceField(choices=[], label="to")
    terms = fields.CharField(max_length=255)
    frequency = fields.ChoiceField(choices=FREQUENCY_CHOICES, initial="", label="Frequency:")
    language = fields.ChoiceField(choices=[], initial="", label="Language:")
    ethnicity = fields.ChoiceField(choices=[], initial="", label="Ethnicity Press:")
    labor = fields.ChoiceField(choices=[], initial="", label="Labor Press:")
    material_type = fields.ChoiceField(choices=[], initial="", label="Material Type:")
    lccn = fields.CharField(max_length=255, label="LCCN:")

    def __init__(self, *args, **kwargs):
        super(SearchTitlesForm, self).__init__(*args, **kwargs)
        current_year = datetime.date.today().year
        years = range(1690, current_year + 1, 10)
        if years[-1] != current_year:
            years.append(current_year)
        choices = [(year, year) for year in years]
        self.fields["year1"].choices = choices
        self.fields["year1"].widget.attrs["class"] = "norm"
        self.fields["year1"].initial = choices[0][0]
        self.fields["year2"].choices = choices
        self.fields["year2"].initial = choices[-1][0]
        self.fields["year2"].widget.attrs["class"] = "norm"

        language = [("", "Select"), ]
        language.extend((l.name, l.name) for l in models.Language.objects.all())
        self.fields["language"].choices = language

        ethnicity = [("", "Select"), ]
        ethnicity.extend((e.name, e.name) for e in models.Ethnicity.objects.all())
        self.fields["ethnicity"].choices = ethnicity

        labor = [("", "Select"), ]
        labor.extend((l.name, l.name) for l in models.LaborPress.objects.all())
        self.fields["labor"].choices = labor

        material = [("", "Select")]
        material.extend((m.name, m.name) for m in models.MaterialType.objects.all())
        self.fields["material_type"].choices = material
