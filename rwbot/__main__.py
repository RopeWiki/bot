import argparse
import glob
import importlib.util
import os

from rwbot.common import AbstractBotAction

import getch
import mwclient


BOT_USER_AGENT = 'RopeWikiBot/0.1 (github.com/RopeWiki/bot)'
MIN_MANUAL_CHANGES = 3


def main():
    # Enumerate available actions
    actions = {}
    actions_glob = os.path.join(os.path.split(__file__)[0], 'actions/*.py')
    for filename in glob.glob(actions_glob):
      if '__init__' in filename:
        continue
      module_name = os.path.splitext(os.path.split(filename)[-1])[0]
      spec = importlib.util.spec_from_file_location(module_name, filename)
      actions[module_name] = importlib.util.module_from_spec(spec)
      spec.loader.exec_module(actions[module_name])

    # Parse arguments from the command line
    parser = argparse.ArgumentParser()
    parser.add_argument('--action', type=str, choices=actions.keys(), help='action for bot to take')
    parser.add_argument('--site', type=str, help='RopeWiki site to act upon')
    parser.add_argument('--scheme', type=str, choices=('http', 'https'), default='https')
    parser.add_argument('--username', type=str, help='Username of bot account through which changes will be applied', default=os.environ.get('RWBOT_USERNAME'))
    parser.add_argument('--password', type=str, help='Password of bot account', default=os.environ.get('RWBOT_PASSWORD'))
    args = parser.parse_args()

    if not args.username:
      raise ValueError('Missing username argument or RWBOT_USERNAME environment variable')
    if not args.password:
      raise ValueError('Missing password argument or RWBOT_PASSWORD environment variable')

    # Load the requested action
    action_module = actions.get(args.action, None)
    if not action_module:
      raise ValueError('No module named %s could be loaded' % args.action)
    if not hasattr(action_module, 'BotAction'):
      raise ValueError('Module %s does not appear to have a class named BotAction defined in it' % args.action)
    action = action_module.BotAction()
    if not isinstance(action, AbstractBotAction):
      raise ValueError('Module %s\'s BotAction does not implement AbstractBotAction defined in common.py' % args.action)

    # Connect to the requested site
    site = mwclient.Site(args.site, path='/', scheme=args.scheme, clients_useragent=BOT_USER_AGENT)

    # Identify changes to make
    changes = action.propose_modifications(site)
    print('Identified %d changes to make.' % len(changes))

    # Apply changes after confirming
    site.login(args.username, args.password)
    changes_committed = 0
    changes_remaining = len(changes) + 1
    committing_all = False
    for change in changes:
      changes_remaining -= 1
      print('===============================================================================')
      change.preview(site)

      commit = False
      if not committing_all:
        suffix = ', apply (a)ll %d remaining changes' % changes_remaining if changes_committed >= MIN_MANUAL_CHANGES else ''
        print('Commit this change? (y)es, (n)o, (q)uit' + suffix)
        complete = False
        while True:
          answer = getch.getch()
          if answer == 'y':
            commit = True
          elif answer == 'n':
            print('Skipping this change.')
          elif answer == 'q':
            complete = True
          elif answer == 'a' and changes_committed >= MIN_MANUAL_CHANGES:
            print('Are you SURE you want to commit %d changes?  Enter "yes, commit %d changes" to continue' % (changes_remaining, changes_remaining))
            verify = input()
            if verify == 'yes, commit %d changes' % changes_remaining:
              committing_all = True
            else:
              print('Verification was not typed correctly.  You must type the content in quotes exactly.')
              continue
          else:
            continue
          break
        if complete:
          break

      if commit or committing_all:
        print('Committing change...')
        change.commit(site)
        changes_committed += 1

    print('Committed %d change%s successfully.' % (changes_committed, '' if changes_committed == 1 else 's'))

if __name__ == '__main__':
    main()
