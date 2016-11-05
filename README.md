Overview
--------

Utility to export intraday heart-rate data from Fitbit. I wrote it for personal
use, but it might be useful for someone else.

Setup
-----

Obtain API keys from Fitbit at `https://dev.fitbit.com` for a "Personal"
type application.

API keys come in the form of a Client ID and a Client Secret. Store these
in `~/secrets/fitbit-api-keys/fitbit.yaml` in a YAML file formatted like this:

    client_id: 123AB4
    client_secret: 0123456789abcdef0123456789abcdef

Note that to access intraday heart rate data you need to have your API keys
whitelisted by Fitbit. You can contact Fitbit support at `api@fitbit.com` to
request this whitelisting. 

Installing dependencies
-----------------------

Set up a virtualenv and install the requirements of the applications by doing
`virtualenv env` and then `pip install -r requirements.txt` in the checked-out
directory.

Scraping data
-------------

Scrape data by running the following command (substituting the date from which
you want to start scraping):

    python fetch_hr.py --begin_from 2016-01-01

When you first do this you will need to authenticate with your Fitbit
credentials; the script will open a login page in your browser (use --browser
if you wish to use a browser other than `google-chrome`).

Data will be saved in the directory specified with --output_datadir, by default
./output-data. Data is saved in the form of the JSON structures returned from
the Fitbit API.

If you're scraping many days, you will get throttled by Fitbit's rate limits
eventually (currently, after 150 requests). The scraping program will exit with
an exception; you can continue by doing `python fetch_hr.py --fill_gaps`.

Exporting to CSV
----------------

You should specify the --timezone flag to get (mostly) correct timestamps.
Fitbit data is stored in a timezone-unaware manner; this implies data loss
whenever you change timezone and inconclusive results for an hour when
there's a DST change. Hopefully your Fitbit is being kept in one particular
time zone; specify that one as the flag.

Use a command like the following to create a CSV from already-scraped data:

    python hr_to_csv.py --timezone Europe/Dublin --output /tmp/my-data.csv

License
-------

Copyright 2016 Steinar V. Kaldager (steinarvkaldager@gmail.com)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Legal notice
------------

This program is not a Google product; is not endorsed by Google, should not
be associated with Google officially or unofficially, and was not written
using Google resources, time, or equipment.

