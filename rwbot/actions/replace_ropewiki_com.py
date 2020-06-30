import re

from rwbot.common import AbstractBotAction, ChangePageText


class BotAction(AbstractBotAction):
  """Finds instances of "ropewiki.com" and replaces them with {{SERVER}} or {{SERVERNAME}}."""

  def propose_modifications(self, site):
    hits = site.search(search='ropewiki.com', what='text')
    changes = []
    for hit in hits:
      title = hit['title']
      old_text = site.pages[title].text()
      new_text = replace_ropewiki(old_text)
      if new_text != old_text:
        change = ChangePageText(title, new_text, 'Replace ropewiki.com with SERVER and SERVERNAME magic words')
        changes.append(change)
    return changes


def replace_ropewiki(text):
  text = re.sub(r'http://ropewiki\.com', lambda m: '{{SERVER}}', text)

  exclusions = ('luca.',)
  def replace_match(m):
    for exclude in exclusions:
      i0 = m.regs[0][0]
      if i0 >= len(exclude) and text[i0 - len(exclude):i0] == exclude:
        return text[i0:m.regs[0][1]]
    return '{{SERVERNAME}}'
  text = re.sub(r'(?i)ropewiki\.com', replace_match, text)
  return text
