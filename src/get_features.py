from itertools import chain


class FeatureTemplate:
  """
  Base feature template class, which must have:
  * A structural specifier, in XPath, specifying *where* in the input tree to look
  * List of attributes of the resulting nodes to look at; default None => all
  """
  def __init__(self):
    self.label = None
    self.xpath = '//node'
    self.subsets = None

  def apply(self, root):
    """
    Simple un-optimized function which takes in a FeatureTemplate object and an xml object
    and returns a feature set
    """
    # Optionally take subsets of the node set (e.g. n-grams) 
    res = root.xpath(self.xpath)
    res_sets = [res] if self.subsets is None else subsets(res, self.subsets)

    # Generate the features
    for res_set in res_sets:
      yield self._feat_str(res_set)

  def _feat_str(self, res_set):
    return '%s[%s]' % (self.label, '_'.join(map(str, res_set)))

  def __repr__(self):
    return "<%s, XPath='%s', attrib=%s, subsets=%s>" % (self.label, self.xpath, self.attrib, self.subsets)


def subsets(x, L):
  """
  Return all subsets of length 1, 2, ..., min(l, len(x)) from x
  """
  return chain.from_iterable([x[s:s+l+1] for s in range(len(x)-l)] for l in range(min(len(x),L)))


class Mention(FeatureTemplate):
  """
  The feature comprising the set of nodes making up the mention
  """
  def __init__(self, cid):
    self.label = 'MENTION'
    self.xpath = ".//node[@cid='%s']" % str(cid)
    self.subsets = 100  # Take n-grams for *all* n...


class Get(FeatureTemplate):
  """
  Returns the map of a specific node attribute onto the resulting node set
  This is assumed to be the outermost feature template class
  Given this, Get uses the apply function of the input feature template
  """
  def __init__(self, f, attrib):
    self.f = f
    self.f.label = '%s-%s' % (attrib.upper(), f.label)
    self.f.xpath = f.xpath + '/@' + attrib

  def apply(self, root):
    return self.f.apply(root)


class Left(FeatureTemplate):
  """
  The feature comprising the set of nodes to the left of the input feature's nodes
  Inherits the input feature's attribs if not specified otherwise
  """
  def __init__(self, f):
    self.label = 'LEFT-OF-%s' % f.label
    self.xpath = f.xpath + '/preceding-sibling::node'
    self.subsets = 3


class Right(FeatureTemplate):
  """
  The feature comprising the set of nodes to the right of the input feature's nodes
  Inherits the input feature's attribs if not specified otherwise
  """
  def __init__(self, f):
    self.label = 'RIGHT-OF-%s' % f.label
    self.xpath = f.xpath + '/following-sibling::node'
    self.subsets = 3


class Between(FeatureTemplate):
  """
  The set of nodes *between* two node sets
  """
  def __init__(self, f1, f2):
    self.label = 'BETWEEN-%s-%s' % (f1.label, f2.label)
    self.xpath = '/ancestor::node'
    self.xpath1 = f1.xpath
    self.xpath2 = f2.xpath
    self.subsets = None

  def apply(self, root):
    """
    Get the path between the two node sets by getting the lowest shared parent,
    then concatenating the two ancestor paths at this shared parent
    """
    p1 = root.xpath(self.xpath1 + self.xpath)
    p2 = root.xpath(self.xpath2 + self.xpath)
    shared = set(p1).intersection(p2)
    b1 = []
    b2 = []
    for node in reversed(p1):
      b1.append(node)
      if node in shared: break
    for node in reversed(p2):
      if node in shared: break
      b2.append(node)
    return [self._feat_str(b1 + b2[::-1])]