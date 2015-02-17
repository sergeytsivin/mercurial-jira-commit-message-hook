# -*- coding: utf-8
import re
from mercurial import demandimport
demandimport.disable()
import requests
demandimport.enable()
import json
from datetime import datetime

# If the hook returns True - hook fails
BAD_COMMIT = True
OK = False

# List of the available JIRA projects
JIRA_PROJECTS = ['TASK']

JIRA_USERNAME = 'stsivin'
JIRA_PASSWORD = '*****'
JIRA_ENDPOINT = 'https://jira.rbc.ru/rest/api/latest'
HG_REPO_PREFIX = 'http://hg.rbc.ru'


def post_commit_message(issue_key, comment):
    url = '%s/issue/%s/comment' % (JIRA_ENDPOINT, issue_key)

    headers = {'content-type': 'application/json'}
    data = json.dumps({'body': comment})
    auth = (JIRA_USERNAME, JIRA_PASSWORD)

    r = requests.post(url, data, auth=auth, headers=headers, verify=False)
    print r.json()


def extract_issue_keys(msg):
    """
    Finds references to JIRA tickets
    :param msg: commit description
    :return:
    """
    re_names = '|'.join(['%s-\d+' % name for name in JIRA_PROJECTS])
    p = re.compile(r'\b(%s)\b' % re_names)
    return p.findall(msg)


def format_comment(repo, rev):
    node = repo[rev]
    url = '%s/%s/rev/%s' % (HG_REPO_PREFIX, repo.root, node.hex())
    comment = 'Committed at revision: [%d|%s]\n' % (node.rev(), url)
    comment += '{noformat}\n'
    comment += 'branch: %s\n' % node.branch()
    comment += 'user: %s\n' % node.user()
    comment += 'date: %s\n' % datetime.fromtimestamp(int(node.date()[0])).strftime('%c')
    comment += 'summary: %s\n' % node.description()
    comment += '{noformat}\n'

    return comment


def process_commit(ui, repo, rev):
    msg = repo[rev].description()
    issues = extract_issue_keys(msg)
    comment = format_comment(repo, rev)
    ui.warn('%s\n' % comment)
    for key in issues:
        post_commit_message(key, comment)


def change_group_hook(ui, repo, node, **kwargs):
    """
    For pull: checks commit messages for all incoming commits
    It is good for master repo, when you pull a banch of commits

    [hooks]
    changegroup.jiranotify =
        python:/path/jirakeycheck.py:change_group_hook
    """

    # import sys
    # sys.path.append('/www/hook-test/pycharm-debug.egg')
    # import pydevd
    # pydevd.settrace('172.28.128.1', port=7070, stdoutToServer=True, stderrToServer=True)
    #
    for rev in xrange(repo[node].rev(), len(repo)):
        process_commit(ui, repo, rev)
    return OK


def pretxncommit_hook(ui, repo, **kwargs):
    """
    Checks commit message for matching commit rule:
    Every commit message must include JIRA issue key
    Example:

    PRJ-42 added meaning of life

    [hooks]
    pretxncommit.jirakeycheck = python:/path/jirakeycheck.py:pretxncommit_hook
    """
    hg_commit_message = repo['tip'].description()
    if check_message(hg_commit_message) is False:
        print_usage(ui)
        return BAD_COMMIT # reject commit transaction
    else:
        return OK


def check_message(msg):
    """
    Checks message for matching regex

    Commit should reference at least one jira key
    """
    issues = extract_issue_keys(msg)
    return len(issues) > 0


def print_usage(ui):
    ui.warn('=====\n')
    ui.warn('Commit message must have JIRA issue key\n')
    ui.warn('Example:\n')
    ui.warn('PRJ-42 - the answer to life, universe and everything \n')
    ui.warn('=====\n')


if __name__ == '__main__':
    post_commit_message('TASK-3373', 'Test commit')