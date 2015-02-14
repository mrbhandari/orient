from django.conf.urls import patterns, include, url
from views import user_profile

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'mysite.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^profile/$', user_profile),
   
        )
