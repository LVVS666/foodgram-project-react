from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()


class GroupAdminForm(forms.ModelForm):
    """Form for change user's groups."""
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=FilteredSelectMultiple('users', False)
    )

    class Meta:
        exclude = []
        model = Group

    def __init__(self, *args, **kwargs):
        super(GroupAdminForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['users'].initial = self.instance.user_set.all()

    def save(self, *args, **kwargs):
        instance = super(GroupAdminForm, self).save()
        self.save_m2m()

        return instance

    def save_m2m(self):
        """
        Inasmuch where is only 1 group - STAFF - changing it for user means
        is_staff = reversed is_staff.
        """
        for user in self.instance.user_set.all():
            user.is_staff = not user.is_staff
            user.save()
        self.instance.user_set.set(self.cleaned_data['users'])
