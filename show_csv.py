import pandas
import sys
import datetime
import matplotlib.pyplot as plt
import gflags

FLAGS = gflags.FLAGS

gflags.DEFINE_string("input_csv", "", "input CSV filename")
gflags.DEFINE_integer("horizon", 86400, "lookback horizon (in seconds)")

if __name__ == "__main__":
  FLAGS(sys.argv)
  assert FLAGS.input_csv
  df = pandas.read_csv(FLAGS.input_csv, parse_dates=["time"])
  utcCutoff = datetime.datetime.utcnow() - datetime.timedelta(seconds=FLAGS.horizon)
  df = df[df.time.notnull()]
  df = df[df.time > utcCutoff]
  df.plot("time", "heartrate")
  plt.show()
