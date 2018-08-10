from django import forms
from django.forms import widgets
from django.contrib.auth import authenticate,get_user_model

class LoginForm(forms.Form):
    username = forms.CharField(
        required=True,
        max_length=128,
        widget=widgets.TextInput(
            attrs={
            'class':'form-control',
            'placeholder':'用户名',
            'required':"true"
            }
        )
    )
    password = forms.CharField(
        required=True,
        widget=widgets.PasswordInput(
            attrs={
                'type':'password',
                'class':'form-control',
                'placeholder':'密码',
                'required': "true"
            }
        )
    )
    valid_code = forms.CharField(
        required=True,
        max_length=4,
        min_length=4,
        widget=widgets.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': '验证码',
                'required': "true"
            }
        )
    )


    def clean(self):

        valid_code_from_session = self._request.session['valid_code']

        if self.cleaned_data['valid_code'].lower() != valid_code_from_session.lower():
            self.add_error("valid_code","验证码错误")
        else:
            user_model = get_user_model()
            user_obj = user_model.objects.filter(username=self.cleaned_data['username'])
            if user_obj:
                if user_obj.first().check_password(self.cleaned_data['password']):
                    authenticate(username=self.cleaned_data['username'], password=self.cleaned_data['password'])
                else:
                    self.add_error('password','密码不正确')

            else:
                self.add_error('username', '用户不存在')



