# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, include, url
from django.conf.urls.static import static
from django.conf import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    
    # project specific urls  (index, impressum, etc)
    url(r'^$', 'PROJECTNAME.apps.views.index', name='index'),
    
    # app specific urls
    url(r'^APP/', include('PROJECTNAME.apps.APPNAME.urls')),
    
    url(r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    urlpatterns = urlpatterns + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)