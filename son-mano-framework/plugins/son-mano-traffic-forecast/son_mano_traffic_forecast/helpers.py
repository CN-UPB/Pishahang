import requests
import json
import logging
from dateutil import parser

# logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("plugin:tfp")

def run_async(func):
    """
            run_async(func)
                    function decorator, intended to make "func" run in a separate
                    thread (asynchronously).
                    Returns the created Thread object

                    E.g.:
                    @run_async
                    def task1():
                            do_something

                    @run_async
                    def task2():
                            do_something_too

                    t1 = task1()
                    t2 = task2()
                    ...
                    t1.join()
                    t2.join()
    """
    from threading import Thread
    from functools import wraps

    @wraps(func)
    def async_func(*args, **kwargs):
        func_hl = Thread(target=func, args=args, kwargs=kwargs)
        func_hl.start()
        return func_hl

    return async_func

def get_netdata_charts(instance_id, vim_endpoint, _charts_parameters):
    netdata_url = "http://{host}:19999/api/v1/charts".format(host=vim_endpoint)
    r = requests.get(netdata_url, verify=False)

    # LOG.info("netdata_url")
    # LOG.info(netdata_url)
    # LOG.info(r.text)

    # _charts_parameters = ["cpu", "net_eth0"]
    if r.status_code == requests.codes.ok:
        _result_json = json.loads(r.text)
        charts = [key for key in _result_json['charts'].keys() if instance_id in key.lower()]
        # Select only the monitoring parameters
        charts = [_c for _c in charts if any(_cp in _c for _cp in _charts_parameters)]
        return charts
    else:
        return []

def get_netdata_charts_instance(charts, vim_endpoint, avg_sec=0, gtime=60):
    # http://vimdemo1.cs.upb.de:19999/api/v1/data?chart=cgroup_qemu_qemu_127_instance_0000007f.net_tap0c32c278_4e&gtime=60
    _chart_avg_url = "http://{host}:19999/api/v1/data?chart={chart_id}&format=json&after=-{last_sec_avg}&gtime={gtime}"

    _instance_metrics = {}

    for _c in charts:
        LOG.info(_chart_avg_url.format(host=vim_endpoint,
                                       chart_id=_c, last_sec_avg=avg_sec, gtime=gtime))
        _c_name = _c.split(".")[1]
        r = requests.get(_chart_avg_url.format(
            host=vim_endpoint, chart_id=_c, last_sec_avg=avg_sec, gtime=gtime), verify=False)
        if r.status_code == requests.codes.ok:
            _result_json = json.loads(r.text)
            if "net" in _c_name:
                if "packets" in _c_name:
                    _instance_metrics["packets"] = _result_json
                else:
                    _instance_metrics["net"] = _result_json
            else:
                _instance_metrics[_c_name] = _result_json

    return _instance_metrics
