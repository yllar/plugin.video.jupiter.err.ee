import urlparse
import urllib2

def download_url(self, url):
  for retries in range(0, 5):
    try:
      r = urllib2.Request(url.encode('iso-8859-1', 'replace'))
      r.add_header('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:10.0.2) Gecko/20100101 Firefox/10.0.2')
      u = urllib2.urlopen(r, timeout=30)
      contents = u.read()
      u.close()
      return contents
    except Exception, ex:
      if retries > 5:
        raise EtvException(ex)