import fitbit.api
import yaml
import re
import errno
import datetime
import json
import urlparse
import gflags
import sys
import os.path
import threading
import time
import subprocess

from BaseHTTPServer import (HTTPServer, BaseHTTPRequestHandler)

FLAGS = gflags.FLAGS

gflags.DEFINE_string("secrets", "~/secrets/fitbit-api-keys/fitbit.yaml", "location of Fitbit secrets")
gflags.DEFINE_string("browser", "google-chrome", "command to run as browser")
gflags.DEFINE_string("output_datadir", "./output-data", "directory to put output data")
gflags.DEFINE_integer("horizon_days", 30, "days back to look")
gflags.DEFINE_string("begin_from", "", "as an alternative to horizon_days, specify the yyyy-mm-dd day on which to start")
gflags.DEFINE_bool("fill_gaps", False, "as an alternative to horizon_days, fill any gaps in the downloaded sequence")
gflags.DEFINE_bool("exclude_today", True, "exclude today's data (since it might be incomplete)")

def read_yaml(filename):
  with open(os.path.expanduser(filename)) as f:
    return yaml.safe_load(f)

def fitbit_login_url(creds, redirect_to):
  oa = fitbit.api.FitbitOauth2Client(creds["client_id"], creds["client_secret"])
  url, _ = oa.authorize_token_url(redirect_uri=redirect_to)
  return url

def token_from_path(creds, path, redirected_to):
  oa = fitbit.api.FitbitOauth2Client(creds["client_id"], creds["client_secret"])
  params = urlparse.parse_qs(urlparse.urlparse(path).query)
  oa.fetch_access_token(params["code"][0], redirected_to)
  return oa.token

def obtain_token(creds, browser):
  paths = []
  class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
      paths.append(self.path)
  httpd = HTTPServer(("", 8080), CallbackHandler)
  def serve_http():
    httpd.serve_forever()
  bg = threading.Thread(target=serve_http)
  bg.daemon = True
  bg.start()
  redirect_uri = "http://127.0.0.1:8080/"
  url = fitbit_login_url(creds, redirect_uri)
  subprocess.call([browser, url])
  while not paths:
    time.sleep(1)
    if not paths:
      print "Waiting for redirected connection.."
  httpd.shutdown()
  return token_from_path(creds, paths[0], redirect_uri)

def make_fitbit(creds, token):
  return fitbit.api.Fitbit(
    creds["client_id"],
    creds["client_secret"],
    access_token=token["access_token"],
    refresh_token=token["refresh_token"])

def obtain_fitbit(secrets_file, browser):
  creds = read_yaml(secrets_file)
  token = obtain_token(creds, FLAGS.browser)
  return make_fitbit(creds, token)

def fetch_daily_heart_rate(fb, date):
  datestamp = date.strftime("%Y-%m-%d")
  url = "https://api.fitbit.com/1/user/-/activities/heart/date/{}/1d/1sec.json".format(datestamp)
  return fb.make_request(url)

def mkdir_p(path):
  try:
    os.makedirs(path)
  except OSError as e:
    if e.errno == errno.EEXIST and os.path.isdir(path):
      pass
    else:
      raise

def make_data_path(basepath, resource, date):
  datestamp = date.strftime("%Y-%m-%d")
  return os.path.join(basepath,
    resource, "{}-{}.json".format(resource, datestamp))

def ensure_heartrate_downloaded(fb, basepath, date):
  assert (datetime.datetime.now().date() > date) or (not FLAGS.exclude_today)
  filename = make_data_path(basepath, "heartrate", date)
  mkdir_p(os.path.dirname(filename))
  if os.path.exists(filename):
    with open(filename) as f:
      return json.load(f)
  data = fetch_daily_heart_rate(fb, date)
  with open(filename, "w") as f:
    f.write(json.dumps(data, indent=2))
  return data

def dates_within_horizon(n, nowdate=None, exclusive=True):
  nowdate = nowdate or datetime.datetime.now().date()
  ago = nowdate - datetime.timedelta(days=n)
  for t in dates_from(ago, nowdate, exclusive=exclusive):
    yield t

def next_day(d):
  return d + datetime.timedelta(days=1)


def dates_from(startdate, nowdate=None, exclusive=True):
  nowdate = nowdate or datetime.datetime.now().date()
  if not exclusive:
    nowdate = next_day(nowdate)
  t = startdate
  while t < nowdate:
    yield t
    t = next_day(t)

def parse_date(s):
  return datetime.datetime.strptime(s, "%Y-%m-%d").date()

def find_gap(basepath, resource):
  names = os.listdir(os.path.join(basepath, resource))
  pattern = re.compile(resource + "-(....-..-..)\.json")
  dates = []
  for name in names:
    m = pattern.match(name)
    if m:
      dates.append(parse_date(m.group(1)))
  dates.sort()
  for i in range(len(dates)-1):
    nd = next_day(dates[i])
    if dates[i+1] != nd:
      return nd
  return None

if __name__ == "__main__":
  FLAGS(sys.argv)
  fb = obtain_fitbit(FLAGS.secrets, FLAGS.browser)
  exclusive = FLAGS.exclude_today
  if FLAGS.begin_from:
    dates = dates_from(parse_date(FLAGS.begin_from), exclusive=exclusive)
  elif FLAGS.fill_gaps:
    gap_date = find_gap(FLAGS.output_datadir, "heartrate")
    print "First gap:", gap_date
    dates = dates_from(gap_date, exclusive=exclude)
  else:
    dates = dates_within_horizon(FLAGS.horizon_days, exclusive=exclusive)
  for date in dates:
    data = ensure_heartrate_downloaded(fb, FLAGS.output_datadir, date)
    points = len(data["activities-heart-intraday"]["dataset"])
    print "{}: {} data points".format(date, points)
