# WH Monitor

### Web Health Monitor for periodic check web resources and collect metrics

This service provides functionality for periodical web resources check, collect metrics (status code, response time, etc.)
and send them to Kafka, PostgreSQL or on any other way through defined loaders.

## Usage

All job entries are placed in the `schedule.yaml`. Structure of each entry:
url - target url to check
schedule - cron like schedule. The format is the same as in regular cron jobs, except you have ability to specify
           period in seconds on the six place (like with `* * * * * */30` schedule job will be run in every 30 seconds)
body_regex - optional field with regular expression to examine response's body
