#!/usr/bin/env python
#
#
# depends on a triage.cfg file in pwd with something like:
#
# {
#	"owner": "mozilla",
#	"repo": "rust",
#	"gh_user": "<you>",
#	"gh_pass": "<yourpasswd>"
# }
#
# 
import json
import urllib2
import sys
import re
import logging, logging.handlers
import github
from time import strftime, gmtime
from os import mkdir

def main():

    fmt = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(message)s',
                            datefmt="%Y-%m-%d %H:%M:%S %Z")

    if "--quiet" not in sys.argv:
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        sh.setLevel(logging.DEBUG)
        logging.root.addHandler(sh)

    rfh = logging.handlers.RotatingFileHandler("triage.log",
                                               backupCount=10,
                                               maxBytes=1000000)
    rfh.setFormatter(fmt)
    rfh.setLevel(logging.DEBUG)
    logging.root.addHandler(rfh)
    logging.root.setLevel(logging.DEBUG)

    logging.info("---------- starting run ----------")
    logging.info("loading triage.cfg")
    cfg = json.load(open("triage.cfg"))

    try:
        mkdir("issues")
        logging.info("created dir issues/")
    except OSError:
        pass

    gh = github.GitHub(username=cfg["gh_user"].encode("utf8"),
                       password=cfg["gh_pass"].encode("utf8"))

    owner = cfg["owner"].encode("utf8")
    repo = cfg["repo"].encode("utf8")

    logging.info("loading issues")
    more = True
    page = 1
    with_comments = []

    while more:
        issues = gh.repos(owner)(repo).issues().get(per_page=100,
                                                    page=page)
        page += 1
        logging.info("loaded %d issues" % len(issues))

        if len(issues) == 0:
            more = False

        for issue in issues:
            num = issue["number"]
            title = issue["title"].encode("utf8")
            url = issue["html_url"].encode("utf8")
            body = issue["body"].encode("utf8")
            labels = [ j["name"].encode("utf8") for j in issue["labels"] ]
            user = issue["user"]["login"].encode("utf8")
            created = issue["created_at"].encode("utf8")
            updated = issue["updated_at"].encode("utf8")
            comments = issue["comments"]
            if comments != 0:
                with_comments.append(num)

            f = open("issues/issue-%d.txt" % num, "w")
            f.write("number: " + str(num))
            f.write("\ntitle: " + title)
            for label in labels:
                f.write("\nlabel: " + label)
            f.write("\nfrom: " + user)
            f.write("\ncreated: " + created)
            f.write("\nupdated: " + updated)
            f.write("\nurl: " + url)
            f.write("\n\n")
            f.write(body)
            f.write("\n")
            f.close()


    logging.info("fetching comments on %d issues" % len(with_comments))

    for issue in with_comments:
        logging.info("fetching comments for issue %d" % issue)
        comments = gh.repos(owner)(repo).issues(issue).comments().get(per_page=100)
        fn = "issues/issue-%d.txt" % issue
        f = open(fn, "a+")
        for comment in comments:
            body = comment["body"].encode("utf8")
            user = comment["user"]["login"].encode("utf8")
            created = comment["created_at"].encode("utf8")
            f.write("\n---- " + user + " : " + created + " ----")
            f.write("\n\n" + body)
            f.write("\n")
        f.close()
        logging.info("wrote %d comments to %s" % (len(comments), fn))


if __name__ == "__main__":
    main()

