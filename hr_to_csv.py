import json
import gflags
import pytz
import datetime
import pandas
import sys
import glob

FLAGS = gflags.FLAGS

gflags.DEFINE_string("timezone", "Europe/Dublin", "time zone to interpret Fitbit data as")
gflags.DEFINE_string("output", "", "CSV output file")
gflags.DEFINE_list("input_files", ["./output-data/heartrate/heartrate-*.json"], "input files")

COLUMNS = ["naiveDate", "naiveTime", "time", "timeAssumingNoDST", "utcTimestamp", "heartrate"]

EPOCH = datetime.datetime(1970, 1, 1, tzinfo=pytz.utc)

def records_in_json(tz, filename):
  with open(filename) as f:
    data = json.load(f)
  heartActivities = data["activities-heart"]
  assert len(heartActivities) == 1
  date = heartActivities[0]["dateTime"]
  intraday = data["activities-heart-intraday"]
  assert intraday["datasetType"] == "second"
  assert intraday["datasetInterval"] == 1
  for entry in intraday["dataset"]:
    value = entry["value"]
    timestampStr = date + " " + entry["time"]
    timestamp = datetime.datetime.strptime(timestampStr, "%Y-%m-%d %H:%M:%S")
    try:
      timestampNoDST = trueTimestamp = tz.localize(timestamp, is_dst=None).astimezone(pytz.utc)
    except pytz.exceptions.AmbiguousTimeError:
      trueTimestamp = None
      timestampNoDST = tz.localize(timestamp, is_dst=False).astimezone(pytz.utc)
    utcTimestamp = None
    if trueTimestamp:
      utcTimestamp = (trueTimestamp - EPOCH).total_seconds()
    yield date, entry["time"], trueTimestamp, timestampNoDST, utcTimestamp, value

def records_in_jsons(tz, filename_globs):
  for filename_glob in filename_globs:
    filenames = glob.glob(filename_glob)
    assert filenames
    for filename in filenames:
      for entry in records_in_json(tz, filename):
        yield entry

if __name__ == "__main__":
  FLAGS(sys.argv)
  assert FLAGS.output
  tz = pytz.timezone(FLAGS.timezone)
  records = records_in_jsons(tz, FLAGS.input_files)
  df = pandas.DataFrame(records, columns=COLUMNS)
  df = df.sort_values(["naiveDate", "naiveTime"])
  df.to_csv(FLAGS.output, index=False)
