#!/usr/bin/env python2.7

import smtplib
import datetime
import subprocess
import json
import random
import github
import re
from email.mime.text import MIMEText

cfg = json.load(open("triage.cfg"))

gh = github.GitHub(username=cfg["gh_user"].encode("utf8"),
                   password=cfg["gh_pass"].encode("utf8"))

owner = cfg["owner"].encode("utf8")
repo = cfg["repo"].encode("utf8")

n = 0
users = cfg["users"]
for user in users:
    n += users[user]


more = True
page = 1
issues = []
issue_num_set = set()
while more:
    print "fetching 100 bugs..."
    tmp_issues = gh.repos(owner)(repo).issues().get(direction='asc',
                                                    sort='updated',
                                                    per_page=100,
                                                    page=page)
    for issue in tmp_issues:
        i = int(issue["number"])
        if i in issue_num_set:
            print "DUPE: #%d" % i
        else:
            issues.append(issue)
            issue_num_set.add(i)

    page += 1
    if len(issues) == 0:
        more = False
    if len(issues) > n:
        more = False

print "got %d bugs" % len(issues)
random.shuffle(issues)
date = datetime.date.today().isoformat()

smtp = cfg["smtp_server"].encode("utf8")
sender = cfg["smtp_user"].encode("utf8")
server = smtplib.SMTP_SSL(smtp, 465)
server.set_debuglevel(True)
server.connect(smtp, 465)
server.ehlo()
server.login(sender, cfg["smtp_pass"].encode("utf8"))

for user in users:
    k = users[user]
    bugs = []
    while len(bugs) < k and len(issues) != 0:
        issue = issues.pop()
        num = issue["number"]
        desc = issue["title"].encode("utf8")
        bugs.append("  - [ ] %5s: %s\n               http://github.com/%s/%s/issues/%s\n" %
                    (num, desc,                      owner, repo,   num))
    assert(len(bugs) != 0)
    assert(k != 0)
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

Note: only after all the above has been attempted and no improvements can
be made then you may 'bump' the bug by leaving a comment such as 'bumping
for triage'.

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
