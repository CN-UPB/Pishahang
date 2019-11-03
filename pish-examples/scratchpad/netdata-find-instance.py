import json
import requests

# TODO: make verify=false as a fallback
HOST = "serverdemo2.cs.upb.de"
LAST_SEC_AVG = 30
INSTANCE_ID = "578cf5c9-455c-4351-ae82-7b03482468f3"

netdata_url = "http://{host}:19999/api/v1/charts".format(host=HOST)
r = requests.get(netdata_url, verify=False)

if r.status_code == requests.codes.ok:
    print("success")
    _result_json = json.loads(r.text)
    charts = [key for key in _result_json['charts'].keys() if INSTANCE_ID in key.lower()]

print(charts)

_chart_avg_url = "http://{host}:19999/api/v1/data?chart={chart_id}&format=json&after=-{last_sec_avg}&points=1"

_instance_metrics = {}

for _c in charts:
    print(_c.split(".")[1])
    r = requests.get(_chart_avg_url.format(host=HOST, chart_id=_c, last_sec_avg=LAST_SEC_AVG), verify=False)
    if r.status_code == requests.codes.ok:
        _result_json = json.loads(r.text)
        _instance_metrics[_c.split(".")[1]] = _result_json
        print(_result_json)

print(_instance_metrics)


# http://sonatavim.cs.upb.de:19999/api/v1/data?chart=cgroup_qemu_qemu_31_instance_0000001f.cpu&format=json&after=-60&points=1

