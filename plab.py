#!/usr/bin/env python2

import argparse
import json
import netrc
import os
import Queue
import socket
import sys
import threading
import time
import xmlrpclib
from math import radians, cos, sin, asin, sqrt

parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=
"""Examples:

* Display all sites and nodes that are alive:

%(prog)s --nodes show

* Display the hostnames of nodes that are alive:

%(prog)s --nodes show-hostnames

* Display the IP addresses of nodes that are alive:

%(prog)s --nodes show-ips

* Force a refresh of the cached info about nodes:

%(prog)s --refresh

* Display raw info about a node:

%(prog)s --node icnalplabs2.epfl.ch --raw

* Display the live nodes on which a slice has been installed:

%(prog)s --slice epfl_tomo --nodes show

* Install a slice to a node:

%(prog)s --slice epfl_tomo --add icnalplabs2.epfl.ch

* Install a slice to a list of nodes:

%(prog)s --slice epfl_tomo --add icnalplabs1.epfl.ch,icnalplabs2.epfl.ch

* Install a slice to all nodes:

%(prog)s --slice epfl_tomo --add listed --nodes suggest

* Uninstall a slice from a node:

%(prog)s --slice epfl_tomo --remove icnalplabs1.epfl.ch

* Uninstall a slice from a list of nodes:

%(prog)s --slice epfl_tomo --remove icnalplabs1.epfl.ch,icnalplabs2.epfl.ch

* Uninstall a slice from all live nodes:

%(prog)s --slice epfl_tomo --remove listed --nodes show

* Suggest a list of nodes on which to install a slice (one node per site):

%(prog)s --slice epfl_tomo --nodes suggest

* Upload a file to all nodes of a slice (in the home directory):

%(prog)s --slice epfl_tomo --upload example.txt

* Upload a file to all nodes of a slice (in a specific remote location):

%(prog)s --slice epfl_tomo --upload example.txt --path ~/somewhere

* Check which nodes of a slice are alive right now (executes "hostname" on each):

%(prog)s --slice epfl_tomo --run

* Run a command on each node of a slice:

%(prog)s --slice epfl_tomo --run whoami

* Open a shell to a node of a slice:

%(prog)s --slice epfl_tomo --shell icnalplabs1.epfl.ch

* Upload a file and execute it on each node of a slice:

%(prog)s --slice epfl_tomo --install file
""")

parser.add_argument("--node", default="",
                    help="Displays information about a node. Parameter: node hostname.")
parser.add_argument("--nodes", default="", choices=["show", "show-hostnames", "show-ips", "suggest"],
                    help="Displays information about sites and nodes. Can be used with --slice.")
parser.add_argument("--slice", default="",
                    help="Performs operations on the given slice. Parameters: the slice name. "
                         "Can be used with --nodes.")
parser.add_argument("--run", default="", const="hostname", nargs="?",
                    help="Runs a command on each node of the slice. Can only be used with --slice.")
parser.add_argument("--upload", default="",
                    help="Uploads a file to all nodes of the slice. Can only be used with --slice.")
parser.add_argument("--install", default="",
                    help="Uploads a file to all nodes of the slice and executes it. Can only be used with --slice.")
parser.add_argument("--path", default="~",
                    help="Specifies the remote path for --upload. Default: ~.")
parser.add_argument("--remove", default="",
                    help="Removes node(s) from a slice. "
                         "Parameter: comma-separated list of node hostnames. Can only be used with --slice.")
parser.add_argument("--add", default="",
                    help="Adds node(s) to the slice. Parameter: comma-separated list of node hostnames. "
                         "Can only be used with --slice. Use 'listed' and --nodes to batch select nodes.")
parser.add_argument("--raw", action="store_true",
                    help="Show raw slice data. Can only be used with --slice.")
parser.add_argument("--refresh", action="store_true",
                    help="Forces a refresh of the cached data at each operation. Slow.")
parser.add_argument("--shell", default="",
                    help="Opens a shell to a slice's node. Parameter: node hostname. "
                         "Can only be used with --slice.")
args = parser.parse_args()

server = xmlrpclib.ServerProxy('https://www.planet-lab.eu/PLCAPI/', allow_none=True)
login, account, password = netrc.netrc().authenticators("planet-lab.eu")
auth = {}
auth['AuthMethod'] = 'password'
auth['Username'] = login
auth['AuthString'] = password

cfgdir = os.path.expanduser('~') + '/.plab'
cacheMaxAge = 1 * 3600

try:
  os.makedirs(cfgdir)
except Exception as e:
  pass

def getCachedSites():
  sites = []
  try:
    with open(cfgdir + '/sites.json', 'r') as f:
      if args.refresh or os.path.getmtime(f.name) < time.time() - cacheMaxAge:
        print >> sys.stderr, "Sites cache too old, refreshing..."
        raise Exception("refresh")
      sites = json.load(f)
    print >> sys.stderr, "Loaded %d sites from cache" % len(sites)
  except Exception as e:
    if str(e) != "refresh":
      print >> sys.stderr, "Could not load sites from cache"
      print e
    try:
      sites = server.GetSites(auth)
    except Exception as e:
      with open(cfgdir + '/sites.json', 'r') as f:
        sites = json.load(f)
    print >> sys.stderr, "Loaded %d sites from server" % len(sites)
    try:
      with open(cfgdir + '/sites.json', 'w') as f:
        json.dump(sites, f, indent=2, separators=(',', ': '))
    except Exception as e:
      print >> sys.stderr, "Could not save sites to cache"
  return sites

def getCachedNodes():
  nodes = []
  try:
    with open(cfgdir + '/nodes.json', 'r') as f:
      if args.refresh or os.path.getmtime(f.name) < time.time() - cacheMaxAge:
        print >> sys.stderr, "Nodes cache too old, refreshing..."
        raise Exception("refresh")
      nodes = json.load(f)
    print >> sys.stderr, "Loaded %d nodes from cache" % len(nodes)
  except Exception as e:
    if str(e) != "refresh":
      print >> sys.stderr, "Could not load nodes from cache"
      print >> sys.stderr, e
    try:
      serverNodes = server.GetNodes(auth, {'boot_state': 'boot'})
      nodes = []
      for node in serverNodes:
        if node["boot_state"] == "boot" and (not node["last_contact"] or node["last_contact"] >= time.time() - 7200):
          nodes.append(node)
        else:
          print "Node unresponsive: " + node["hostname"] + " last_contact " + str(node["last_contact"]) + " vs current time " + str(time.time()) + " delta " + str((time.time() - node["last_contact"]) / 3600.) + " hours "
    except Exception as e:
      print e
      with open(cfgdir + '/nodes.json', 'r') as f:
        nodes = json.load(f)
    print >> sys.stderr, "Loaded %d nodes from server" % len(nodes)
    try:
      with open(cfgdir + '/nodes.json', 'w') as f:
        json.dump(nodes, f, indent=2, separators=(',', ': '))
    except Exception as e:
      print >> sys.stderr, "Could not save nodes to cache"
  return nodes

def getSlice(name):
  slice = []
  try:
    slice = server.GetSlices(auth, {'name': name})
    return slice[0]
  except Exception as e:
    print >> sys.stderr, "Could not find slice with name %s" % name
    return False

def addSliceToNodes(slice, nodes):
  try:
    if not server.AddSliceToNodes(auth, slice, nodes):
      raise Exception("error")
  except Exception as e:
    print >> sys.stderr, "Could not add slice %s to node(s) %s" % (name, str(nodes))
    return False

def removeSliceFromNodes(slice, nodes):
  try:
    if not server.DeleteSliceFromNodes(auth, slice, nodes):
      raise Exception("error")
  except Exception as e:
    print >> sys.stderr, "Could not remove slice %s from node(s) %s" % (name, str(nodes))
    return False

def haversine(lat1, lon1, lat2, lon2):
  try:
    # Calculates the distance between two points on a sphere (given as degrees)
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r
  except Exception as e:
    return 1.0e99

def refreshNodes():
  old = args.refresh
  args.refresh = True
  getCachedNodes()
  args.refresh = old

sites = getCachedSites()
nodes = getCachedNodes()

sites.sort(key=lambda site: haversine(site["latitude"], site["longitude"], 46.5198, 6.6335))

slice = None
if args.slice:
  slice = getSlice(args.slice)
  if args.raw:
    print json.dumps(slice, indent=2, separators=(',', ': '))

if args.node:
  for node in nodes:
    if node["hostname"] == args.node:
       print json.dumps(node, indent=2, separators=(',', ': '))

listed_nodes = []
if args.nodes == "show":
  for site in sites:
    empty = True
    for node in nodes:
      if node["site_id"] == site["site_id"]:
        if not slice or slice["slice_id"] in node["slice_ids"]:
          if empty:
            print site["name"].encode("latin1", "replace"), " - ", site["url"]
            empty = False
          print "  ", node["hostname"]
          listed_nodes.append(node["hostname"])

elif args.nodes == "suggest":
  for site in sites:
    empty = True
    for node in nodes:
      if node["site_id"] == site["site_id"]:
        if slice and slice["slice_id"] not in node["slice_ids"]:
          if empty:
            print site["name"].encode("latin1", "replace"), " - ", site["url"]
            empty = False
          print "  ", node["hostname"]
          listed_nodes.append(node["hostname"])

elif args.nodes == "show-hostnames":
  for node in nodes:
    if not slice or slice["slice_id"] in node["slice_ids"]:
      print node["hostname"]
      listed_nodes.append(node["hostname"])

elif args.nodes == "show-ips":
  for node in nodes:
    if not slice or slice["slice_id"] in node["slice_ids"]:
      try:
        ip = socket.gethostbyname(node["hostname"])
        listed_nodes.append(node["hostname"])
        print ip
      except socket.error:
        pass

deploy_run_result = {}
def deploy_run_worker():
  global deploy_run_result
  while True:
    hostname, deploy, cmd = q.get()
    if not hostname:
      return
    deploy_run_result[hostname] = 0
    if deploy:
      deploy_run_result[hostname] = os.system(deploy)
      if deploy_run_result[hostname] != 0:
        return
    if cmd:
      deploy_run_result[hostname] = os.system(cmd)

def parallel_deploy_run(q):
  global deploy_run_result
  deploy_run_result = {}
  threads = [ threading.Thread(target=deploy_run_worker) for i in range(50) ]
  for thread in threads:
    thread.start()
    q.put((None, None, None))
  for thread in threads:
    thread.join()
  failNodes = []
  goodNodes = []
  for hostname in deploy_run_result:
    ret = deploy_run_result[hostname]
    if ret != 0:
      failNodes.append(hostname)
    else:
      goodNodes.append(hostname)
  if failNodes:
    print "Failed for", len(failNodes), "nodes:", ",".join(failNodes)
  else:
    print "All tasks finished successfully."
  if goodNodes:
    print "Worked for", len(goodNodes), "nodes:", ",".join(goodNodes)
  else:
    print "No task finished successfully."

if args.upload:
  assert slice
  q = Queue.Queue()
  result = {}
  for node in nodes:
    if slice["slice_id"] in node["slice_ids"]:
      q.put((node["hostname"], 'scp -o ConnectTimeout=5 -o ConnectionAttempts=1 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "%s" "%s@%s:%s"' % (args.upload, slice["name"], node["hostname"], args.path), None))
  parallel_deploy_run(q)

if args.run:
  assert slice
  q = Queue.Queue()
  result = {}
  for node in nodes:
    if slice["slice_id"] in node["slice_ids"]:
      q.put((node["hostname"], None, 'ssh -o ConnectTimeout=5 -o ConnectionAttempts=1 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o PasswordAuthentication=no "%s@%s" \'%s\'' % (slice["name"], node["hostname"], 'export PATH=~/bin:$PATH; ' + args.run)))
  parallel_deploy_run(q)

if args.install:
  assert slice
  q = Queue.Queue()
  result = {}
  for node in nodes:
    if slice["slice_id"] in node["slice_ids"]:
      q.put((node["hostname"], 'scp -o ConnectTimeout=5 -o ConnectionAttempts=1 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "%s" "%s@%s:%s"' % (args.install, slice["name"], node["hostname"], args.path), 'ssh -o ConnectTimeout=5 -o ConnectionAttempts=1 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "%s@%s" \'%s\'' % (slice["name"], node["hostname"], 'export PATH=~/bin:$PATH; ' + './' + args.install)))
  parallel_deploy_run(q)

if args.add:
  assert slice
  if args.add == "listed":
    nodesRequested = listed_nodes
  else:
    nodesRequested = args.add.split(",")
  print "Adding slice to " + str(len(nodesRequested)) + " nodes..."
  addSliceToNodes(slice["name"], nodesRequested)
  refreshNodes()

if args.remove:
  assert slice
  if args.remove == "listed":
    nodesRequested = listed_nodes
  else:
    nodesRequested = args.remove.split(",")
  print "Removing slice from " + str(len(nodesRequested)) + " nodes..."
  removeSliceFromNodes(slice["name"], nodesRequested)
  refreshNodes()

if args.shell:
  assert slice
  os.system('ssh -o ConnectTimeout=5 -o ConnectionAttempts=1 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "%s@%s"' % (slice["name"], args.shell))
