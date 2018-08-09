class A(object):


    def d(fun):
        def wrap(self,*args,**kwargs):
            pass

            return fun(self,*args,**kwargs)


        return wrap

    @d
    def f(self,job_name):
        print('ffff',job_name)


a = A()
a.f('job1')