# -------------------------------------------------------------------------------
# Copyright IBM Corp. 2018
# 
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
# http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -------------------------------------------------------------------------------

try:
    HAS_UNICODE_TYPE = type(unicode) and True
    str23 = lambda s: str(s)
    bytes23 = lambda s: bytes(s)
    zip23 = zip
    map23 = map
    filter23 = filter
except NameError:
    HAS_UNICODE_TYPE = False
    def bytes23(s):
        if isinstance(s, str):
            return bytes(s, encoding='UTF-8')
        elif isinstance(s, bytes):
            return s
        else:
            raise ValueError('obj not str or bytes: ' + repr(type(s)))
    def str23(s):
        if isinstance(s, str):
            return s
        elif isinstance(s, bytes):
            return str(s, encoding='UTF-8')
        else:
            raise ValueError('obj not str or bytes: ' + repr(type(s)))
    def zip23(*args):
        return list(zip(*args))
    def map23(fn, *args):
        return list(map(fn, *args))
    def filter23(fn, *args):
        return list(filter(fn, *args))
