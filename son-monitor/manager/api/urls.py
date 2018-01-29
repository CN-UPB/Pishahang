from django.conf.urls import url, include
from rest_framework.urlpatterns import format_suffix_patterns
from api import views

# API endpoints
urlpatterns2 = [

    url(r'^api/v1/users$', views.SntUsersList.as_view()),
	url(r'^api/v1/users/(?P<pk>[0-9]+)/$', views.SntUsersDetail.as_view()),
	url(r'^api/v1/users/type/(?P<type>[^/]+)/$', views.SntUserPerTypeList.as_view()),
	url(r'^api/v1/user/(?P<pk>[0-9]+)/$', views.SntUserList.as_view()),

    url(r'^api/v1/services$', views.SntServicesList.as_view()),
    url(r'^api/v1/services/user/(?P<usrID>[^/]+)/$', views.SntServicesPerUserList.as_view()),
    url(r'^api/v1/services/(?P<sonata_srv_id>[^/]+)/$', views.SntServicesDetail.as_view()),

    url(r'^api/v1/service/new$', views.SntNewServiceConf.as_view()),
    url(r'^api/v1/service/(?P<srvID>[^/]+)/$', views.SntServiceList.as_view()),

    url(r'^api/v1/cloud-services$', views.SntCloudServicesList.as_view()),
    url(r'^api/v1/cloud-services/(?P<pk>\d+)$', views.SntCloudServicesDetail.as_view()),

    url(r'^api/v1/functions$', views.SntFunctionsList.as_view()),
    url(r'^api/v1/functions/service/(?P<srvID>[^/]+)/$', views.SntFunctionsPerServiceList.as_view()),

    url(r'^api/v1/metrics$', views.SntMetricsList.as_view()),
    url(r'^api/v1/metrics/function/(?P<funcID>[^/]+)/$', views.SntMetricsPerFunctionList.as_view()),

    url(r'^api/v1/alerts/rules$', views.SntRulesList.as_view()),
    url(r'^api/v1/alerts/rules/service/(?P<srvID>[^/]+)/$', views.SntRulesPerServiceList.as_view()),
    url(r'^api/v1/alerts/rules/service/(?P<srvID>[^/]+)/configuration$', views.SntRuleconf.as_view()),
    url(r'^api/v1/alerts/rule/(?P<sonata_srv_id>[^/]+)/$', views.SntRulesDetail.as_view()),

    url(r'^api/v1/notification/types$', views.SntNotifTypesList.as_view()),
    url(r'^api/v1/notification/type/(?P<pk>[0-9]+)/$', views.SntNotifTypesDetail.as_view()),
    url(r'^api/v1/notification/smtp/component/(?P<component>[^/]+)/$', views.SntSmtpList.as_view()),
    url(r'^api/v1/notification/smtp$', views.SntSmtpCreate.as_view()),
    url(r'^api/v1/notification/smtp/(?P<pk>[0-9]+)/$', views.SntSmtpDetail.as_view()),

    url(r'^api/v1/pop$', views.SntPOPList.as_view()),
    url(r'^api/v1/pop/splatform/(?P<spID>[^/]+)/$', views.SntPOPperSPList.as_view()),
    url(r'^api/v1/pop/(?P<sonata_pop_id>[^/]+)/$', views.SntPOPDetail.as_view()),  # karpa

    url(r'^api/v1/splatform$', views.SntSPList.as_view()),
    url(r'^api/v1/splatform/(?P<pk>[0-9]+)/$', views.SntSPDetail.as_view()),

    url(r'^api/v1/prometheus/metrics/list$', views.SntPromMetricList.as_view()),
    url(r'^api/v1/prometheus/metrics/name/(?P<metricName>[^/]+)/$', views.SntPromMetricDetail.as_view()),
    url(r'^api/v1/prometheus/metrics/data$', views.SntPromMetricData.as_view()),
    url(r'^api/v1/prometheus/configuration$', views.SntPromSrvConf.as_view()),

    url(r'^api/v1/prometheus/pop/(?P<popID>[^/]+)/metrics/list$', views.SntPromMetricPerPOPList.as_view()),
    url(r'^api/v1/prometheus/pop/(?P<popID>[^/]+)/metrics/name/(?P<metricName>[^/]+)/$',
        views.SntPromMetricPerPOPDetail.as_view()),
    url(r'^api/v1/prometheus/pop/(?P<popID>[^/]+)/metrics/data$', views.SntPromMetricPerPOPData.as_view()),
    url(r'^api/v1/prometheus/pop/(?P<popID>[^/]+)/configuration$', views.SntPromSrvPerPOPConf.as_view()),

    url(r'^api/v1/ws/new$', views.SntWSreq.as_view()),
    url(r'^api/v1/ws/pop/(?P<popID>[^/]+)/new$', views.SntWSreqPerPOP.as_view()),  # karpa
]

public_apis = format_suffix_patterns(urlpatterns2)

urlpatterns1 = [
    url(r'^api/v1/internal/smtp/creds/(?P<component>[^/]+)$', views.SntCredList.as_view()),
]

internal_apis = format_suffix_patterns(urlpatterns1)
