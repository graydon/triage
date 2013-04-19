#!/usr/bin/env python2.7

import smtplib
import datetime
import subprocess
import json
import random
import re
from email.mime.text import MIMEText

cfg = json.load(open("triage.cfg"))

smtp = cfg["smtp_server"].encode("utf8")
sender = cfg["smtp_user"].encode("utf8")
server = smtplib.SMTP_SSL(smtp, 465)
server.set_debuglevel(True)
server.connect(smtp, 465)
server.ehlo()
server.login(sender, cfg["smtp_pass"].encode("utf8"))

repo = cfg["gh_repo"].encode("utf8")
n = 0
users = cfg["users"]
for user in users:
    n += users[user]

print "grabbing %d most-forgotten bugs from %s" % (n, repo)
out = subprocess.check_output("ghi list --sort updated --reverse --no-pulls -- %s | head -n %d"
                              % (repo, n+1),
                              shell=True)

all_bugs = [line for line in out.split("\n") if re.match("^ *\d+:", line)]
random.shuffle(all_bugs)
date = datetime.date.today().isoformat()

for user in users:
    k = users[user]
    bugs = []
    while len(bugs) < k and len(all_bugs) != 0:
        bug = all_bugs.pop().strip()
        (num, desc) = bug.split(':', 1)
        bugs.append("%7s:%s\n         http://github.com/%s/issues/%s\n" %
                    (num, desc,                      repo,       num))
    msg = MIMEText(("""Greetings %s contributor!

This week's triage assignment is %d bugs randomly divided between %d people,
based on their preferred weekly capacity. You have been assigned %d bugs.
Please make some time to look through your set and look for ways to move
the bugs forward:

  - Search for duplicates and close the less-clear one if found
  - Search for similar bugs and link them together if found
    (with a comment mentioning the #NNNN number of one bug in the other)
  - Check the tags, title and description for clarity and precision
  - Nominate for a milestone if it fits the milestone's criteria
  - Add testcases, narrow them down or attempt to reproduce failures
  - Provide suggestions on how to fix the bug

And finally:

  - Actually try to fix the bug, if it seems within reach

We recommend using https://github.com/stephencelis/ghi for command-line
operations on bugs. If you have any questions about your assigned bugs,
please drop in to IRC and ask about them.

Your %d bugs for this week are:

%s
""" %
(repo, n, len(users), len(bugs), len(bugs), "\n".join(bugs))))

    msg["Subject"] = "bug inspection assignment for %s on %s" % (repo, date)
    msg["From"] = sender
    msg["To"] = user
    msg["Reply-To"] = sender
    server.sendmail(sender, user, msg.as_string())

server.quit()
