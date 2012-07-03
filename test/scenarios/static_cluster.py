#!/usr/bin/python
import sys, os, time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir, 'common')))
import http_admin, driver, workload_runner, scenario_common
from vcoptparse import *

op = OptParser()
scenario_common.prepare_option_parser_mode_flags(op)
op["use-proxy"] = BoolFlag("--use-proxy")
op["num-nodes"] = IntFlag("--num-nodes", 3)
op["num-shards"] = IntFlag("--num-shards", 2)
op["workload"] = PositionalArg()
op["timeout"] = IntFlag("--timeout", 600)
opts = op.parse(sys.argv)

with driver.Metacluster() as metacluster:
    cluster = driver.Cluster(metacluster)
    executable_path, command_prefix  = scenario_common.parse_mode_flags(opts)
    print "Starting cluster..."
    processes = [driver.Process(cluster, driver.Files(metacluster, db_path = "db-%d" % i, executable_path = executable_path, command_prefix = command_prefix), executable_path = executable_path, log_path = "serve-output-%d" % i, command_prefix = command_prefix)
        for i in xrange(opts["num-nodes"])]
    if opts["use-proxy"]:
        proxy_process = driver.ProxyProcess(cluster, 'proxy-logfile', executable_path = executable_path, log_path = 'proxy-output', command_prefix = command_prefix)
        processes.append(proxy_process)
    for process in processes:
        process.wait_until_started_up()

    print "Creating namespace..."
    http = http_admin.ClusterAccess([("localhost", p.http_port) for p in processes])
    dc = http.add_datacenter()
    for machine_id in http.machines:
        http.move_server_to_datacenter(machine_id, dc)
    ns = http.add_namespace(protocol = "memcached", primary = dc)
    for i in xrange(opts["num-shards"] - 1):
        http.add_namespace_shard(ns, chr(ord('a') + 26 * i // opts["num-shards"]))
    http.wait_until_blueprint_satisfied(ns)

    host, port = driver.get_namespace_host(ns.port, processes if not opts["use-proxy"] else [proxy_process])
    workload_runner.run(opts["workload"], host, port, opts["timeout"])

    cluster.check_and_stop()
