from django.forms import ModelForm
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class CreateUserForm(UserCreationForm):
# class CreateUserForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs = {'class': 'form-control', 'placeholder': field.label}

    class Meta:
        model = User
        fields = ['username', 'password']  # 就两个输入框
        # widgets = {
        #     'name': forms.TextInput(attrs={'class': 'form-control'})
        # }


# class LoginForm(forms.ModelForm):
#     password = forms.CharField(widget=forms.PasswordInput)
#     class Meta:
#         model = User
#         fields = ['username', 'password']
#
#     def clean(self):
#         username = self.cleaned_data.get('username')
#         password = self.cleaned_data.get('password')
#         user = authenticate(username=username, password=password)
#         if user is None:
#             raise forms.ValidationError('Username or password is not correct')
#         return super(LoginForm, self).clean()