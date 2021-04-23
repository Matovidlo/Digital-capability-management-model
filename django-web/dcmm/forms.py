from bootstrap_datepicker_plus import DatePickerInput
from django import forms


class GithubForm(forms.Form):
    repositories = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple)

    def __init__(self, repositories, *args, **kwargs):
        super(GithubForm, self).__init__(*args, **kwargs)
        choices = []
        for repository in repositories:
            choices.append((repository, repository))
        self.fields['repositories'] = forms.MultipleChoiceField(required=True,
                                                                widget=forms.CheckboxSelectMultiple,
                                                                choices=choices)
        self.fields['repositories'].label = 'Repositories'


class ToDoForm(forms.Form):
    date = forms.DateField(
     widget=DatePickerInput(format='%m/%d/%Y')
    )
