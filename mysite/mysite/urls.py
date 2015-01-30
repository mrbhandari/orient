from django.conf.urls import patterns, include, url
from django.contrib import admin
from views import render_home, login, auth_view, logout, loggedin, invalid_login, series, set_post_status_series


urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'mysite.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', render_home),
    
    # user auth urls
    url(r'^accounts/login/$',  login),
    url(r'^accounts/auth/$',  auth_view),    
    url(r'^accounts/logout/$', logout),
    url(r'^accounts/loggedin/$', loggedin),
    url(r'^accounts/invalid/$', invalid_login),
    url(r'^ajax/series/?$', series, name='series'),
    url(r'^ajax/set_post_status_series/?$', set_post_status_series, name='set_post_status_series'),
    
        )
