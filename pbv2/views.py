from django.views import View
from django.shortcuts import render,HttpResponseRedirect,reverse,HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import logout

from .forms import LoginForm
from .utils import ValidCodeImg


class IndexView(LoginRequiredMixin,View):

    def get(self,request):
        return render(request,'base/base.html')


class GetValidImgView(View):
    def get(self,request):
        obj = ValidCodeImg()
        img_data,valid_code = obj.getValidCodeImg()
        request.session['valid_code'] = valid_code
        return HttpResponse(img_data,content_type='image/jpeg')


class LoginView(View):
    def get(self,request):
        login_form = LoginForm()
        return render(request,'login.html',locals())


    def post(self,request):

        login_form = LoginForm(request.POST)
        login_form._request = request
        if login_form.is_valid():
            return HttpResponseRedirect(reverse('index'))
        return render(request,'login.html',{"login_form":login_form})



class LogoutView(LoginRequiredMixin,View):
    def get(self,request):
        logout(request)
        return HttpResponseRedirect(reverse('user_login'))


