# -*- coding: utf-8 -*-
from django.shortcuts import get_object_or_404, render, redirect
from django.conf import settings
from django.template import Template
from .models import *
from .forms import *
from .tasks import *

from django.core.cache import cache
from fandjango.views import authorize_application
from fandjango.decorators import facebook_authorization_required
from fandjango.models import User
from django.db.models import F, Q
from django.http import Http404, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from facepy import GraphAPI, SignedRequest
from facepy.exceptions import FacepyError, FacebookError
from django.db import IntegrityError
from django.utils import simplejson
from django.utils.translation import ugettext as _

from fandjango.utils import get_post_authorization_redirect_url
from haystack.query import SearchQuerySet
from bs4 import BeautifulStoneSoup
from django.template import RequestContext, Template

import datetime
import urllib
import random
import logging
import json
from random import shuffle

logger = logging.getLogger('eintraege')

from .redishelper import get_redis
redis = get_redis()

def global_dict(request):
    # categorygroups = CategoryGroup.objects.all() # deal version
    
    categorygroups = DealCategory.objects.all()
    urlaubsdealskat = UrlaubsguruKategorie.objects.all()
    
    if request.facebook and request.facebook.user:
        profil = request.facebook.user.profil
        
        randomfriends = list(redis.smembers('friends:%s' % request.facebook.user.id))
        shuffle(randomfriends)
    else:
        profil = None
        randomfriends = None
    
  
    
    return {
        'categorygroups': categorygroups,
        'urlaubsdealskat': urlaubsdealskat,
        'profil': profil,
        'randomfriends': randomfriends[:8] if randomfriends else [],
    }

def index(request, id=None):
    
    # nur mit permission gehts rein, oder wenns facebook ist!
    if request.method == 'GET' and request.META.get('HTTP_USER_AGENT', '').startswith('facebookexternalhit'):
        return render(request, 'danke.html', {})
    else:	
        if not request.facebook or not request.facebook.user:
            return authorize_application(
                        request = request,
                        redirect_uri= get_post_authorization_redirect_url(request),
            )

# hier noch die anz_notifyclicks zählen für die nutzer

# hier die umleitung auf die seite außerhalb, wenn neueruser == False


    sender = None
    
    profil = Profil.objects.get(user=request.facebook.user)
    
    if profil.geloescht:
        profil.geloescht = False
        profil.save()
    
    # doi setzen wenn aus einer email
    if request.GET.get('doi', False):
        mailinglist_make_doi.delay(
            profil.unique_hash,
            request.META.get('HTTP_X_FORWARDED_FOR', False) or request.META.get('REMOTE_ADDR', ''),
            request.META.get('HTTP_USER_AGENT', 'Unknown')
        )
    
    # hier den nutzer reggen, unique hash holen und dann die willkommen-mail versenden
    if profil.unique_hash == '' and profil.user.email:
        logger.debug(u'User adden und welcome-Mailing verschicken, da unique hash noch nicht gesetzt ist')
        
        mailinglist_add_user_and_welcome.delay(
            profil.id,
            str(request.facebook.user.facebook_id),
            request.facebook.user.email,
            request.facebook.user.full_name,
            request.facebook.user.gender,
            request.META.get('HTTP_X_FORWARDED_FOR', False) or request.META.get('REMOTE_ADDR', ''),
            request.META.get('HTTP_USER_AGENT', 'Unknown'),
            request.facebook.user.locale,
            request.LANGUAGE_CODE,
        )
    
    # gibt es überhaupt requests?
    if request.GET.get('request_ids') and request.GET['request_ids'] != '':
        graph = GraphAPI(settings.FANDJANGO_SECRET_TOKEN)

        try:
            logger.debug(request.GET.get('request_ids'))
            req = graph.get('', ids=request.GET.get('request_ids'))

            redis.incr('num-requests-accepted:%s' % str(datetime.date.today()), len(req))

            for r in req:
                # normale app-generated requests separieren...
                if req[r].has_key('from') and req[r]['from'] != None:
                    # hier den nutzer holen, der den letzten request verschickt hat
                    sender = User.objects.get(facebook_id=req[req.keys()[0]]['from']['id'])
                    # wenn der user bereits angemeldet ist, dann den request löschen
                    delete_request.delay(request.facebook.user.id, r)
                    logger.debug(u'Request gelöscht, user id: %s, request id: %s' % (request.facebook.user.facebook_id, r)) # eq[req.keys()[0]]['id']
                
                    break
        except TypeError:
            logger.debug(u'Das holen der request ids von facebook ist fehlgeschlagen')
        except FacebookError:
            logger.debug(u'Der Request ist nicht mehr gültig...')

    if not sender and id:
        sender = User.objects.get(id=id)

    anz_freunde = redis.scard('friends:%s' % profil.user.id)
    anz_freunde_im_boot = redis.sinter('friends:%s' % profil.user.id, 'appusers')
    
    if request.mobile:
        template = 'danke_mobile.html'
    else:
        template = 'danke.html'
    
    return render(request, template, {
        'profil': profil,
        'friends': random.sample(profil.friends,4 if len(profil.friends)>4 else len(profil.friends)) if profil and profil.friends else {},
        'friends2': random.sample(profil.friends,4 if len(profil.friends)>4 else len(profil.friends)) if profil and profil.friends else {},
        'sender': sender,
        'anz_freunde': anz_freunde,
        'anz_freunde_im_boot':anz_freunde_im_boot,
    })

def uebersicht(request):
    
    die3neusten = Voucher.objects.filter(availability_status=1).order_by('-published')[:5]
    die3besten = Voucher.objects.filter(availability_status=1, flags_top=True).order_by('?')[:5]
    
    deals = Deal.objects.order_by('-date')
    urlaubsdeals = UrlaubsguruDeal.objects.order_by('-date')
    
    return render(request, 'index_neu.html', dict({
        'die3neusten': die3neusten,
        'die3besten': die3besten,
        'deals': deals,
        'urlaubsdeals': urlaubsdeals,
    }, **global_dict(request)))


def kategorie(request, id, subid=None):
    ''' alte gutschein-version
    kat = get_object_or_404(CategoryGroup, id=id)
    
    subkats = kat.categories.all()
    
    if subid:
        subkat = kat.categories.get(id=subid)
        vouchers = subkat.voucher_set.filter(availability_status=1)
    else:
        subkat = None
        vouchers = Voucher.objects.filter(availability_status=1, categorygroup=kat)


    return render(request, 'kategorie_neu.html', dict({
        'kat': kat,
        'subkat': subkat,
        'subkats': subkats,
        'vouchers': vouchers,
    }, **global_dict(request)))
    '''
    kat = get_object_or_404(DealCategory, id=id)
    
    deals = kat.deals.all()
    
    
    return render(request, 'kategorie_neu.html', dict({
        'kat': kat,
        'vouchers': deals,
    }, **global_dict(request)))

def urlaubskategorie(request, id):
    kat = get_object_or_404(UrlaubsguruKategorie, id=id)
    
    deals = kat.urlaubsdeals.all()
    
    return render(request, 'urlaubskategorien.html', dict({
        'kat': kat,
        'vouchers': deals,
    }, **global_dict(request)))

def detail(request, id):
    gutschein = get_object_or_404(Voucher, id=id, availability_status=1)
    gutscheine_shop = Voucher.objects.filter(provider=gutschein.provider, availability_status=1).exclude(id=gutschein.id)
    gutscheine_categorygroup = Voucher.objects.filter(categorygroup=gutschein.categorygroup, availability_status=1).exclude(id=gutschein.id)[:10]
    comments = Comment.objects.filter(voucher=gutschein).order_by('-created')[:3]
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['fb'] == True:
                
                '''
                request.facebook.user.graph.post(
                    path = 'me/gutscheinhippo:comment_on',
                    voucher = 'http://www.dealhippo.de/detail/%s/' % id,
                    message = form.cleaned_data['text']
                )
                '''
            
            comment = form.save(commit=False)
            comment.user = request.facebook.user
            comment.voucher = gutschein
            comment.save()
            return redirect('detail', id=id)
    else:
        form = CommentForm()
    
    return render(request, 'detail_neu.html', dict({
        'gutschein': gutschein,
        'gutscheine_shop': gutscheine_shop,
        'gutscheine_categorygroup': gutscheine_categorygroup,
        'form': form,
        'comments': comments,
    }, **global_dict(request)))

def deals(request):
    deals = Deal.objects.all()
    return render(request, 'deals.html', dict({
            'deals': deals,
        }, **global_dict(request)))

def urlaubsdeals(request):
    deals = UrlaubsguruDeal.objects.all()
    return render(request, 'urlaubsdeals.html', dict({
            'deals': deals,
        }, **global_dict(request)))


def deal(request, id):
    deal = get_object_or_404(Deal, id=id)
    return render(request, 'deal.html', dict({
            'deal': deal,
        }, **global_dict(request)))

def urlaubsdeal(request, id):
    deal = get_object_or_404(UrlaubsguruDeal, id=id)
    return render(request, 'deal.html', dict({
            'deal': deal,
        }, **global_dict(request)))


def iframe(request, id):
    gutschein = get_object_or_404(Voucher, id=id, allowsIframe=True, availability_status=1)

    if request.GET.get('content'):
        return render(request, 'iframe-content.html', dict({
            'gutschein': gutschein,
            
            # ...
            
        }, **global_dict(request)))
    else:
        return render(request, 'iframe.html', dict({
            'gutschein': gutschein,
        }, **global_dict(request)))

def static_content(request, slug):
    content = get_object_or_404(StaticContent, slug=slug).content

    t = Template(content)
    rendered = t.render(RequestContext(request, global_dict(request)))

    return HttpResponse(rendered)

def ajax_typeahead(request):
    q = request.REQUEST.get('q', False)
    if q == False:
        return Http404()
    results = [{'title': r.title, 'url': r.url} for r in SearchQuerySet().autocomplete(title_auto=q)[:5]]

    return HttpResponse(json.dumps(results).replace('&amp;', '&'), mimetype="application/json")

def ajax_voucher(request, id):
    if id.isnumeric():
        u = urllib.urlopen('http://api.sparwelt.de/1.2/singlevoucher/46D1B-3BA84-A827B?filter[id]=%s&requestIp=%s&requestAgent=%s' % (id, request.META['REMOTE_ADDR'], request.META['HTTP_USER_AGENT']))
        bss = BeautifulStoneSoup(u)
        code = bss.find('code').string
        if code.strip() == "no code required":
            code = "Kein Code erforderlich"
        return HttpResponse(code)
    else:
        return HttpResponse('none')

@facebook_authorization_required()
def ajax_friend_notify(request):
    friend_notify_task.delay(request.facebook.user.id, request.GET.get('voucher'))
    return HttpResponse('ok')

@csrf_exempt
def sent_req(request):
    # user mit der id "id" hat requests an alle user in "ids" gesendet
    for id in request.POST['ids'].split(','):
        redis.sadd('requests-sent:%s' % request.POST['id'], id)
        
    redis.incr('num-requests-sent:%s' % str(datetime.date.today()), len(request.POST['ids'].split(',')))
    return HttpResponse('ok')

@csrf_exempt
def deauth(request):
    user_id = SignedRequest.parse(request.REQUEST.get('signed_request'), settings.FACEBOOK_APPLICATION_SECRET_KEY)['user_id']
    logger.debug(u'nutzer mit der id %s will geloescht werden' % user_id)
    try:
        user = User.objects.get(facebook_id=user_id)
    except User.DoesNotExist:
        logger.debug(u'nutzer mit der id %s existiert nicht, kann also auch nicht geloescht werden' % user_id)
        return HttpResponse('everything fine, dear facebook')

    user.profil.geloescht = True
    user.profil.willkommenmailsenden = True
    user.profil.mailsenden = True
    user.profil.anz_eintraege = 0
    user.profil.save()
    
    return HttpResponse('everything fine, dear facebook')

def stopmail(request, unique_hash, fbid):
    try:
        p = Profil.objects.get(user__facebook_id=fbid, unique_hash=unique_hash)
        p.subscribed_for_emails=False
        p.save()
        return HttpResponse('Stopped sending mails to %s' % fbid)
    except Profil.DoesNotExist:
        return HttpResponse('User not found')
        
def req_stats(request):
    
    datas = []
    requests_sent_keys = redis.keys('num-requests-sent:*')
    requests_sent = redis.mget(requests_sent_keys)
    requests_accepted_keys = redis.keys('num-requests-accepted:*')
    requests_accepted = redis.mget(requests_accepted_keys)
    days_sent = [key.split(':')[1] for key in requests_sent_keys]
    days_accepted = [key.split(':')[1] for key in requests_accepted_keys]
    both = set(days_sent) | set(days_accepted)
    for day in both:
        date = day.split('-')
        try:
            num_sent = requests_sent[requests_sent_keys.index('num-requests-sent:%s' % day)]
        except:
            num_sent = 0
        try:
            num_accepted = requests_accepted[requests_accepted_keys.index('num-requests-accepted:%s' % day)]
        except:
            num_accepted = 0
        if num_sent == 0:
            datas.append([date[0], int(date[1])-1, date[2], num_sent, num_accepted, 0])
        else:
            datas.append([date[0], int(date[1])-1, date[2], num_sent, num_accepted, str(round((float(num_accepted)/float(num_sent)*100),2)).replace(',','.')])
    
    datas.sort(key=lambda k: int('%s%s%s' % (k[0], str(k[1]).zfill(2), k[2])))
    
    requests_sent = sum(map(int,requests_sent))
    requests_accepted = sum(map(int,requests_accepted))
    
    return render(request, 'stats.html', {
        'datas': datas,
        'requests_sent': requests_sent,
        'requests_accepted': requests_accepted,
        'crate': float(requests_accepted)/float(requests_sent)*100
    })
    
def neuertask(request):
    if not request.user.is_authenticated():
        return redirect('/admin/?next=/neuertask/')
    
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['minnotificationklicks'] > 0:
                notify_all_users.delay(form.cleaned_data['jobtemplateid'], anz_klicks_min=form.cleaned_data['minnotificationklicks'])
            elif form.cleaned_data['sprache']:
                notify_all_users.delay(form.cleaned_data['jobtemplateid'], lang=form.cleaned_data['sprache'])
            else:
                notify_all_users.delay(form.cleaned_data['jobtemplateid'])
        # hier dann einfach den task starten...
    else:
        form = TaskForm()

    return render(request, 'neuertask.html', {
        'form': form,
    })

def redirecter2(request):
	return HttpResponse('<html><body><script type="text/javascript">window.top.location = "%s";</script></body></html>' % request.GET.get('url'))

@facebook_authorization_required()
def redirecter(request, slug):
    return HttpResponse('<html><body><script type="text/javascript">window.top.location = "http://apps.gefaellt-mir.me/static/notifyRedirect.php?target=%s&locale=%s";</script></body></html>' % (slug, request.facebook.user.locale))