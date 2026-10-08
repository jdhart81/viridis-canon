"""Ordinary injected-opener wait adapter. It never changes transport acceptance.

Only the exact owned, frozen archive PUT receives 600 seconds; every other
request delegates its existing timeout unchanged. No retries or diagnostics
containing headers, credentials, request bodies or environment are added.
"""
import hashlib,re
from digest_metadata import check
ARCHIVE_NAME='METHODS_NOTES.zip'
OWN_ARCHIVE_URL='https://zenodo.org/api/files/1487b1c9-45df-4b52-af5f-d2f7cd123b98/METHODS_NOTES.zip'
ARCHIVE_SHA256='4f0aff85202b32e3b206d20f0aa318f9f8ae01e4e6ea39f25cc6479ce2d35178'
ARCHIVE_SIZE=30500744
class OwnedArchiveWait:
 def __init__(self,opener,url,sha256,size):
  check(url==OWN_ARCHIVE_URL and re.fullmatch(r'https://zenodo[.]org/api/files/[a-f0-9-]{36}/METHODS_NOTES[.]zip',url)is not None,'OWN_ARCHIVE_BUCKET_URL')
  check(sha256==ARCHIVE_SHA256 and type(size)is int and size==ARCHIVE_SIZE,'EXACT_FROZEN_ARCHIVE_WAIT_PROFILE')
  self.opener=opener;self.url=url;self.sha256=sha256;self.size=size
 @property
 def deadline(self):return self.opener.deadline
 @deadline.setter
 def deadline(self,value):self.opener.deadline=value
 def open(self,request,timeout=120):
  check(type(timeout)is int and timeout==120,'UNCHANGED_TRANSPORT_WAIT_DEFAULT')
  method=request.get_method();url=request.full_url
  if method=='PUT' and url.rsplit('/',1)[-1]==ARCHIVE_NAME:
   check(url==self.url and isinstance(request.data,bytes) and len(request.data)==self.size and hashlib.sha256(request.data).hexdigest()==self.sha256,'EXACT_OWN_FROZEN_ARCHIVE_REQUEST_ONLY')
   return self.opener.open(request,timeout=600)
  return self.opener.open(request,timeout=timeout)
