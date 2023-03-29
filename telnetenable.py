#! /usr/bin/env python3

# Copyright (c) 2009 Paul Gebheim
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import sys
import socket
import array
from optparse import OptionParser
import warnings
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.utils import CryptographyDeprecationWarning
from hashlib import md5

warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)

TELNET_PORT = 23

# The version of Blowfish supplied for the telenetenable.c implementation
# assumes Big-Endian data, but the code does nothing to convert the
# little-endian stuff it's getting on intel to Big-Endian
#
# So, since Crypto.Cipher.Blowfish seems to assume native endianness, we need
# to byteswap our buffer before and after encrypting it
#
# This helper does the byteswapping on the string buffer
def ByteSwap(data):
  a = array.array('i')
  if(a.itemsize < 4):
    a = array.array('L')
  
  if(a.itemsize != 4):
    print("Need a type that is 4 bytes on your platform so we can fix the data!")
    exit(1)

  a.frombytes(data)
  a.byteswap()
  return a.tobytes()

def hexdump(bytes):
  line = ""
  for i, b in enumerate(bytes):
    if i % 16 != 0:
      line += " "
      if i % 8 == 0:
        line += "   "
    if i % 16 == 0 and i > 0:
      print(line)
      line = ""
    line += f"{b:02x}"
  if line != "":
    print(line)

def GeneratePayload(mac, username, password=""):
  # eventually reformat mac
  mac = mac.replace(":","").upper()

  # Pad the input correctly
  assert(len(mac) < 0x10)
  just_mac = mac.ljust(0x10, "\x00")

  assert(len(username) <= 0x10)
  just_username = username.ljust(0x10, "\x00")
  
  assert(len(password) <= 0x21)
  just_password = password.ljust(0x21, "\x00")

  cleartext = (just_mac + just_username + just_password).ljust(0x70, '\x00')
  md5_key = md5(cleartext.encode("ascii")).digest()

  payload = ByteSwap((md5_key + cleartext.encode("ascii")).ljust(0x80, b"\x00"))
  
  secret_key = "AMBIT_TELNET_ENABLE+" + password

  cipher = Cipher(algorithms.Blowfish(secret_key.encode("ascii")), modes.ECB())
  encryptor = cipher.encryptor()
  payload_encrypted = encryptor.update(payload) + encryptor.finalize()
  return ByteSwap(payload_encrypted)


def SendPayload(ip, payload):
  for res in socket.getaddrinfo(ip, TELNET_PORT, socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_IP):
    af, socktype, proto, canonname, sa = res
    try:
      s = socket.socket(af, socktype, proto)
    except socket.error as msg:
      s = None
      continue

    try:
      s.connect(sa)
    except socket.error as msg:
      s.close()
      s= None
      continue
    break

  if s is None:
    print("Could not connect to '%s:%d'" % (ip, TELNET_PORT))
  else:
    s.send(payload)
    s.close()
    print("Sent telnet enable payload to '%s:%d'" % (ip, TELNET_PORT))
  
def main():
  args = sys.argv[1:]
  if len(args) < 3 or len(args) > 4:
    print("usage: python telnetenable.py <ip> <mac> <username> [<password>]")
    sys.exit(1)

  ip = args[0]
  mac = args[1]
  username = args[2]

  password = ""
  if len(args) == 4:
    password = args[3]

  payload = GeneratePayload(mac, username, password)
  print("payload:")
  hexdump(payload)
  SendPayload(ip, payload)

if __name__ == "__main__":
  main()
