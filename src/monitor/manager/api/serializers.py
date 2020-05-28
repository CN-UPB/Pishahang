'''
Copyright (c) 2015 SONATA-NFV [, ANY ADDITIONAL AFFILIATION]
ALL RIGHTS RESERVED.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Neither the name of the SONATA-NFV [, ANY ADDITIONAL AFFILIATION]
nor the names of its contributors may be used to endorse or promote 
products derived from this software without specific prior written 
permission.

This work has been performed in the framework of the SONATA project,
funded by the European Commission under Grant number 671517 through 
the Horizon 2020 and 5G-PPP programmes. The authors would like to 
acknowledge the contributions of their colleagues of the SONATA 
partner consortium (www.sonata-nfv.eu).
'''



from rest_framework import serializers
from api.models import *
from api.serializers import *
from django.contrib.auth.models import User
from django.core import serializers as core_serializers

#######################################################################################################

class SntSmtpSerializerCreate(serializers.ModelSerializer):
    class Meta:
        model = monitoring_smtp
        fields = ('id', 'smtp_server', 'port', 'user_name', 'password', 'component', 'sec_type')

class SntSmtpSerializerList(serializers.ModelSerializer):
    class Meta:
        model = monitoring_smtp
        fields = ('id', 'smtp_server', 'port', 'user_name', 'component', 'sec_type', 'created')

class SntSmtpSerializerCred(serializers.ModelSerializer):
    class Meta:
        model = monitoring_smtp
        fields = ('id', 'password')

class SntSPSerializer(serializers.ModelSerializer):
    class Meta:
        model = monitoring_service_platforms
        fields = ('id', 'sonata_sp_id', 'name', 'manager_url','created')

class SntPOPSerializer(serializers.ModelSerializer):
    class Meta:
        model = monitoring_pops
        fields = ('id', 'sonata_pop_id','sonata_sp_id' ,'name', 'prom_url','created')
        lookup_field = 'sonata_pop_id'

class SntUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = monitoring_users
        fields = ('id', 'first_name', 'last_name', 'email', 'sonata_userid', 'created','type','mobile')
        lookup_field = {'email','mobile'}


class SntServicesSerializer(serializers.ModelSerializer):
    #user = serializers.PrimaryKeyRelatedField(read_only=False, queryset=monitoring_users.objects.all())
    #user = SntUserSerializer()
    class Meta:
        model = monitoring_services
        fields = ('id', 'sonata_srv_id', 'name', 'description', 'created', 'user', 'host_id','pop_id')

class SntServicesFullSerializer(serializers.ModelSerializer):
    #user = serializers.PrimaryKeyRelatedField(read_only=False, queryset=monitoring_users.objects.all())
    user = SntUserSerializer()
    class Meta:
        model = monitoring_services
        fields = ('id', 'sonata_srv_id', 'name', 'description', 'created', 'user', 'host_id','pop_id')

class SntCloudServicesSerializer(serializers.ModelSerializer):
    service = serializers.PrimaryKeyRelatedField(read_only=False, queryset=monitoring_services.objects.all())
    class Meta:
        model = monitoring_cloud_services
        fields = ('id', 'cloud_service_record_uuid', 'csd_name', 'vdu_id', 'description', 'created', 'service', 'pop_id')

class SntFunctionsSerializer(serializers.ModelSerializer):
    service = serializers.PrimaryKeyRelatedField(read_only=False, queryset=monitoring_services.objects.all())
    #service = SntServicesSerializer()
    class Meta:
        model = monitoring_functions
        fields = ('id', 'sonata_func_id', 'name', 'description', 'created', 'service', 'host_id','pop_id')

class SntServicesDelSerializer(serializers.ModelSerializer):
    class Meta:
        model = monitoring_services
        fields = ('id', 'sonata_srv_id', 'name', 'description', 'created', 'user', 'host_id','pop_id')
        lookup_field = 'sonata_srv_id'

class SntFunctionsFullSerializer(serializers.ModelSerializer):
    #service = serializers.PrimaryKeyRelatedField(read_only=False, queryset=monitoring_services.objects.all())
    service = SntServicesSerializer()
    class Meta:
        model = monitoring_functions
        fields = ('id', 'sonata_func_id', 'name', 'description', 'created', 'service', 'host_id', 'pop_id')

class SntMetricsSerializer(serializers.ModelSerializer):
    #function = serializers.PrimaryKeyRelatedField(read_only=False, queryset=monitoring_functions.objects.all())
    #function = SntFunctionsSerializer()
    class Meta:
        model = monitoring_metrics
        fields = ('id', 'name', 'description', 'threshold', 'interval','cmd', 'function', 'created',)

class SntNewMetricsSerializer(serializers.ModelSerializer):
    #function = serializers.PrimaryKeyRelatedField(read_only=False, queryset=monitoring_functions.objects.all())
    #function = SntFunctionsSerializer()
    class Meta:
        model = monitoring_metrics
        fields = ('name', 'description', 'threshold', 'interval','cmd', 'function', 'created')

class SntMetricsFullSerializer(serializers.ModelSerializer):
    #function = serializers.PrimaryKeyRelatedField(read_only=False, queryset=monitoring_functions.objects.all())
    function = SntFunctionsSerializer()
    class Meta:
        model = monitoring_metrics
        fields = ('id', 'name', 'description', 'threshold', 'interval','cmd', 'function', 'created',)

class SntMetricsSerializer1(serializers.ModelSerializer):
    sonata_func_id = serializers.PrimaryKeyRelatedField(read_only=False, queryset=monitoring_functions.objects.all())

    class Meta:
        model = monitoring_metrics
        fields = ('id', 'name', 'description', 'threshold', 'interval','cmd', 'sonata_func_id', 'created',)

class SntNotifTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = monitoring_notif_types
        fields = ('id', 'type',)

class SntServicesLightSerializer(serializers.ModelSerializer):
    class Meta:
        model = monitoring_services
        fields = ('sonata_srv_id', 'name')
        lookup_field = 'sonata_srv_id'

class SntRulesSerializer(serializers.ModelSerializer):
    #service = serializers.PrimaryKeyRelatedField(read_only=False, queryset=monitoring_services.objects.all())
    #notification_type = serializers.PrimaryKeyRelatedField(read_only=False, queryset=monitoring_notif_types.objects.all())
    service = SntServicesLightSerializer()
    notification_type = SntNotifTypeSerializer()
    class Meta:
        model = monitoring_rules
        fields = ('id', 'name', 'duration', 'summary', 'description', 'condition', 'notification_type','service', 'created',)


class SntRulesPerSrvSerializer(serializers.ModelSerializer):
    notification_type = SntNotifTypeSerializer()
    class Meta:
        model = monitoring_rules
        fields = ('id', 'name', 'duration', 'summary', 'description', 'condition', 'notification_type', 'created',)

class SntNewFunctionsSerializer(serializers.ModelSerializer):
    #service = serializers.PrimaryKeyRelatedField(read_only=False, queryset=monitoring_services.objects.all())
    #service = SntServicesSerializer()
    metrics = SntNewMetricsSerializer(many=True)
    class Meta:
        model = monitoring_functions
        fields = ('sonata_func_id', 'name', 'description', 'created', 'host_id', 'pop_id', 'metrics')

class SntNewRulesSerializer(serializers.ModelSerializer):
    #service = serializers.PrimaryKeyRelatedField(read_only=False, queryset=monitoring_services.objects.all())
    #function = serializers.PrimaryKeyRelatedField(read_only=False, queryset=monitoring_functions.objects.all())
    #notification_type = serializers.PrimaryKeyRelatedField(read_only=False, queryset=monitoring_notif_types.objects.all())
    class Meta:
        model = monitoring_rules
        fields = ('name', 'duration', 'summary', 'description', 'condition', 'notification_type', 'created',)

class NewServiceSerializer(serializers.Serializer):
    service = SntServicesSerializer()
    functions = SntNewFunctionsSerializer(many=True)
    rules = SntNewRulesSerializer(many=True)

class promMetricLabelSerializer(serializers.Serializer):
    metric_name = ''

class promMetricsListSerializer(serializers.Serializer):
    metrics = promMetricLabelSerializer(many=True)

class promLabelsSerializer(serializers.Serializer):
    labels = {'label':'id'}

class SntPromMetricSerializer(serializers.Serializer):
    name = serializers.CharField()
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()
    labels = promLabelsSerializer(many=True)
    step = serializers.CharField()

class CommentSerializer(serializers.Serializer):
    email = serializers.EmailField()
    content = SntRulesSerializer(many=True)
    created = serializers.DateTimeField()

class wsLabelSerializer(serializers.Serializer):
    label = ''

class SntWSreqSerializer(serializers.Serializer):
    metric = serializers.CharField()
    filters = wsLabelSerializer(many=True)

class SntSPSerializer(serializers.ModelSerializer):
    class Meta:
        model = monitoring_service_platforms
        fields = ('id', 'sonata_sp_id', 'name', 'manager_url','created')

class SntPOPSerializer(serializers.ModelSerializer):
    class Meta:
        model = monitoring_pops
        fields = ('id', 'sonata_pop_id','sonata_sp_id' ,'name', 'prom_url','created')

class SntRulesConfSerializer(serializers.Serializer):
    rules = SntRulesPerSrvSerializer(many=True)
######################################################################################
'''
class TestTBSerializer(serializers.Serializer):
    pk = serializers.IntegerField(read_only=True)
    owner = serializers.ReadOnlyField(source='owner.username')
    title = serializers.CharField(required=False, allow_blank=True, max_length=100)
    code = serializers.CharField(style={'base_template': 'textarea.html'})
    linenos = serializers.BooleanField(required=False)
    language = serializers.ChoiceField(choices=LANGUAGE_CHOICES, default='python')
    style = serializers.ChoiceField(choices=STYLE_CHOICES, default='friendly')

    def create(self, validated_data):
        
        #Create and return a new `Snippet` instance, given the validated data.
        

        return test_tb.objects.create(**validated_data)

    def update(self, instance, validated_data):
        
        #Update and return an existing `Snippet` instance, given the validated data.
        
        instance.title = validated_data.get('title', instance.title)
        instance.code = validated_data.get('code', instance.code)
        instance.linenos = validated_data.get('linenos', instance.linenos)
        instance.language = validated_data.get('language', instance.language)
        instance.style = validated_data.get('style', instance.style)
        instance.save()
        return instance

class UserSerializer(serializers.ModelSerializer):
    snippets = serializers.PrimaryKeyRelatedField(many=True, queryset=test_tb.objects.all())

    class Meta:
        model = User
        fields = ('id', 'username', 'api', 'owner', 'snippets')
'''

'''
{
    "service": {
        "sonata_srv_id": "NS777777",
        "name": "service test1",
        "description": "service test description",
        "host_id": "",
        "sonata_usr_id": "123456"
    },
    "functions": [{
        "sonata_func_id": "NF112233",
        "name": "function test 1",
        "description": "function description",
        "host_id": "555555",
        "metrics": [{
            "name": "metric test 1",
            "description": "metric test description",
            "threshold": 50,
            "interval": 10,
            "units": "kB",
            "cmd": "cmd1"
        }, 
        {
            "name": "metric test 2",
            "description": "metric test description",
            "threshold": 45,
            "interval": 35,
            "units": "kB",
            "cmd": "cmd2"
        }]
    },
    {
        "sonata_func_id": "NF445566",
        "name": "function test 21",
        "description": "function description",
        "host_id": "666666",
        "metrics": [{
            "name": "metric test 3",
            "description": "metric test description",
            "threshold": 46,
            "interval": 23,
            "units": "kB",
            "cmd": "cmd3"
        }, {
            "name": "metric test 4",
            "description": "metric test description",
            "threshold": 89,
            "interval": 34,
            "units": "kB",
            "cmd": "cmd4"
        }]
    }],
    "rules": [{
        "name": "Rule 4",
        "duration": "4m",
        "summary": "Rule sweet rule ",
        "description": "Rule sweet rule ",
        "condition": "metric1-mmetric2> 0.25",
        "notification_type": 2
    },
    {
        "name": "Rule 45",
        "duration": "4m",
        "summary": "Rule sweet rule... ",
        "description": "Rule sweet rule ....",
        "condition": "metric1-mmetrNewServiceSerializeric2> 0.25",
        "notification_type": 2
    }]
}
'''
