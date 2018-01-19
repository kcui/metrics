import collections
import json
import pprint
import requests
import thread
import time

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# paths to metrics that we want to measure
metric_paths =  [#['meters', 'dashbase.ingestion.event.bytes', 'count'],
                 #['meters', 'dashbase.ingestion.event.bytes', 'meanRate'],
                 ['timers', 'dashbase.service.query', 'count'],
                 ['timers', 'dashbase.service.query', 'meanRate']]

# stores totals for averaging
metric_totals = {'.'.join(path) : [] for path in metric_paths}  

def json_get(url):
  """
  Given a URL, utilizes python's requests module to parse the contents of the
  URL as a JSON in dictionary form and returns it.
  """
  headers = {'content-type': 'application/json', 'accept': 'application/json'}
  data = requests.get(url, headers = headers, verify=False).json()
  return data

def get_metric(data, path):
  """
  Given JSON data in dictionary form and a metric path in list form,
  retrieves the measurement that corresponds with the metric path or None
  if the path is invalid in context of data.
  """
  temp = data
  for step in path:
    try:
      temp = temp[step]
    except KeyError:
      return None
  return temp

def reduce(iters):
  """
  Given the number of iterations run, either averages metric_totals
  when considering meanRate or gets the difference of counts (total
  number processed) if considering count
  """
  reduced_metric_totals = metric_totals.copy()
  for k, v in reduced_metric_totals.iteritems():
    if k.endswith("count"):
      reduced_metric_totals[k] = v[-1] - v[0]
    else:
      reduced_metric_totals[k] = sum(v) / iters
  return reduced_metric_totals


def input_thread(L):
  """
  Thread to detect Enter key
  """
  raw_input()
  L.append(None)

def loop(url, iters, interval):
  """
  Takes a URL to poll, the number of iterations, and the time interval
  to sleep between each poll. Prettyprints the average of each of the metrics 
  defined in the global metric_paths upon pressing the Enter key.
  """
  L = []
  thread.start_new_thread(input_thread, (L,))
  i = 0
  while i < iters:
    time.sleep(.1)
    if L:
      print "currently on iteration %d/%d" % (i, iters)
      pprint.pprint(reduce(i))

      # restart thread
      L = []
      thread.start_new_thread(input_thread, (L,))
      
    data = json_get(url)
    for path in metric_paths:
      metric = get_metric(data, path)
      if metric != None:
        metric_totals['.'.join(path)].append(metric)
    i += 1
  thread.exit()

if __name__ == "__main__":
  url = "https://staging.dashbase.io:9876/v1/metrics/vars/" #"https://34.216.97.98:7888/v1/metrics/vars"
  iters = 100
  sleep_interval = 1  # in seconds
  loop(url, iters, sleep_interval)
    