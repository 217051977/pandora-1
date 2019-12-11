from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from .models import Atempt, Team, Contest, Test, get_contest_code_path, TeamMember, Profile


class DateInputWidget(forms.DateTimeInput):
    input_type = 'datetime-local'


class AttemptModelForm(forms.ModelForm):
    comment = forms.CharField(required=False)

    class Meta:
        model = Atempt
        fields = ['file', 'comment']


class CreateContestModelForm(forms.ModelForm):

    class Meta:
        model = Contest
        # widgets = {'start_date': DateInputWidget(), 'end_date': DateInputWidget()}
        fields = "__all__"


class CreateTestModelForm(forms.ModelForm):

    class Meta:
        model = Test
        fields = "__all__"

    def changed_input_file(self, *args, **kwargs):
        input_file = self.changed_data.get('input_file')

        print("****************************************" + str(input_file) + "****************************************")

        return input_file

    def changed_output_file(self, *args, **kwargs):
        output_file = self.changed_data.get('output_file')

        print("****************************************" + str(output_file) + "****************************************")

        return output_file


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(required=True, label='First Name', max_length=30)
    last_name = forms.CharField(required=True, label='Last Name', max_length=150)
    number = forms.IntegerField(required=True, label='Student Number')
    gprd = forms.BooleanField(required=True, initial=False,
                              label='Agree to share my information (name, email, number, username, grade) with the authors and other users of this application')

    class Meta:
        model = User
        fields = ('email', 'username', 'password1', 'password2')


class TeamMemberApprovalForm(forms.Form):
    member_id = forms.CharField(required=False)
    member_id_remove = forms.CharField(required=False)
    team_remove = forms.CharField(required=False)


class TeamMemberForm(forms.Form):
    team_id = forms.CharField(required=True)


class TeamModelForm(forms.ModelForm):
    name = forms.CharField(required=True, label='Team Name')

    class Meta:
        model = Team
        fields = ['name']
