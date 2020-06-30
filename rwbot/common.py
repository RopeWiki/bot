from abc import ABC, abstractmethod
import difflib
from typing import Sequence

import mwclient


class Modification(ABC):
  def __init__(self, change_description: str):
    self.change_description = change_description

  @abstractmethod
  def preview(self, site: mwclient.Site):
    raise NotImplementedError('Modification must implement preview')

  @abstractmethod
  def commit(self, site: mwclient.Site):
    raise NotImplementedError('Modification must implement commit')


class ChangePageText(Modification):
  def __init__(self, title: str, new_text: str, change_description: str):
    super(ChangePageText, self).__init__(change_description)
    self.title = title
    self.new_text = new_text

  def preview(self, site: mwclient.Site):
    old_text = site.pages[self.title].text()
    d = difflib.Differ()
    diff = d.compare(old_text.split('\n'), self.new_text.split('\n'))
    print(self.title + ':')
    print('\n'.join(line for line in diff if not line.startswith(' ')))
    print('(changes above on page "%s")' % self.title)

  def commit(self, site:mwclient.Site):
    site.pages[self.title].edit(self.new_text, self.change_description)


class AbstractBotAction(ABC):
  @abstractmethod
  def propose_modifications(self, site: mwclient.Site) -> Sequence[Modification]:
    raise NotImplementedError('BotAction must implement propose_modifications')
