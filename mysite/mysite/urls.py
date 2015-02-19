from django.conf.urls import patterns, include, url
from django.contrib import admin
from views import render_home, login, auth_view, logout, loggedin, invalid_login, set_post_status_series, return_event_detail, return_user_detail, return_user_event_details, return_user_quad_details,get_graph_data, test_graph_data
from userprofile import urls as userprofileurls


urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'mysite.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/', include(userprofileurls)),
    
    # homepage
    url(r'^$', render_home),
    
    # user auth urls
    url(r'^accounts/login/$',  login),
    url(r'^accounts/auth/$',  auth_view),    
    url(r'^accounts/logout/$', logout),
    url(r'^accounts/loggedin/$', loggedin),
    url(r'^accounts/invalid/$', invalid_login),
    url(r'^ajax/set_post_status_series/?$', set_post_status_series, name='set_post_status_series'),

    # apis for getting graph data
    url(r'^accounts/loggedin/test_graph_data/?$', test_graph_data, name='test_graph_data'),
    url(r'^accounts/loggedin/get_graph_data/?$', get_graph_data, name='get_graph_data'),
    url(r'^accounts/loggedin/get_event_details/?$', return_event_detail, name='get_event_details'),
    url(r'^accounts/loggedin/get_user_details/?$', return_user_detail, name='get_user_details'),
    url(r'^accounts/loggedin/get_user_event_details/?$', return_user_event_details, name='get_user_event_details'),
    url(r'^accounts/loggedin/get_user_quad_details/?$', return_user_quad_details, name='get_user_quad_details'),

        )
