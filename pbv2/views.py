from django.views import View
from django.shortcuts import render,HttpResponseRedirect,reverse,HttpResponse
from django.contrib.auth import authenticate
import copy

from .forms import LoginForm
from .utils import ValidCodeImg


class IndexView(View):

    def get(self,request):
        return render(request,'index.html')


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
            if user is not None:
                if user.is_active:
                    return HttpResponseRedirect(reverse('index'))
                else:
                    return render(request, 'login.html', {"login_form":login_form})


        return render(request,'login.html',{"login_form":login_form})
