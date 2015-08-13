#!/usr/bin/python3
#
# cached_property: a cached property with cache invalidation support
#
# Copyright (C) Almer S. Tigelaar <almer@tigelaar.net>
#
# Implementation of cached_property that automatically invalidates its
# cached value when setting or deleting. This is similar in spirit to this approach
# https://github.com/pydanny/cached-property. However, invalidation is automatic for
# property setters that you define (as well as deleting properties).
#
# Based on a combination of techniques from various sources, notably these two:
# * https://gist.github.com/sharoonthomas/1673907 (Werkzeug Team, BSD Licensed)
# * https://stackoverflow.com/questions/12405087/subclassing-pythons-property (Raymond Hettinger, Public Domain)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import sys
assert sys.version_info.major==3, "cached_property requires Python 3!"

class cached_property(object):
    """This emulates PyProperty_Type() in Objects/descrobject.c,
       adds caching and cache invalidation as well.

       This can be used in the exact same way as property() is used, either
       specifying property(fset, fget, fdel) separately or using decorators.

       WARNING: If you change the variable internally you *MUST* do an explicit
       set (the cached_property can not know when an internal variable is updated).
       Concretely, this means that you can't do this:
 
        class Test:
            def __init__(self):
                self._p = 10

            def inc_p(self):
                self._p += 1

            @cached_property
            def p(self):
                return self._p

            @p.setter
            def p(self, value):
                self._p = value

       When invoking inc_p() this won't be reflected in Test.p (as the value is cached at '10'),
       a call to inc_p() and then to Test.p will return 10, not 11!
  
       The right way to do this is:

            def inc_p(self):
                self.p += 1
       
       This way 'p' itself is updated, the cache is invalidated and Test.p will return 11 after
       inc_p() is invoked.

       Somewhat related, this does not work:

            @cached_property
            def p(self):
                self._p += 1
                return self._p

       Since the value that p returns is cached, subsequent invocation will not execute the getter
       but instead use the cached value. If you want this type of behaviour, you should not use
       cached_property.

       :copyright: (c) 2014 Almer S. Tigelaar
       :license: AGPLv3
    """

    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        self.fget = fget
        self.fset = fset
        self.fdel = fdel
        if doc is None and fget is not None:
            doc = fget.__doc__
        self.__doc__ = doc

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if self.fget is None:
            raise AttributeError("unreadable attribute")
            
        if self.fget.__name__ in obj.__dict__:
            value = obj.__dict__[self.fget.__name__] # Cached
        else:
            value = obj.__dict__[self.fget.__name__] = self.fget(obj) # Set for caching

        return value

    def __set__(self, obj, value):
        if self.fset is None:
            raise AttributeError("can't set attribute")
        self.fset(obj, value)
        if self.fget.__name__ in obj.__dict__:
            del obj.__dict__[self.fget.__name__] # Invalidate any cached value

    def __delete__(self, obj):
        if self.fdel is None:
            raise AttributeError("can't delete attribute")
        self.fdel(obj)
        if self.fget.__name__ in obj.__dict__:
            del obj.__dict__[self.fget.__name__] # Invalidate any cached value

    def getter(self, fget):
        return type(self)(fget, self.fset, self.fdel, self.__doc__)

    def setter(self, fset):
        return type(self)(self.fget, fset, self.fdel, self.__doc__)

    def deleter(self, fdel):
        return type(self)(self.fget, self.fset, fdel, self.__doc__)

if __name__ == '__main__':

    class Test:
        def __init__(self):
            self._p = 10

        @cached_property
        def p(self):
            return self._p

        @p.setter
        def p(self, value):
            self._p = value

    t = Test()
    t.p = 10 # Set
    print(t.p) # Get
    print(t.p) # Cached Get
    t.p = 20 # Set
    print(t.p) # Get
    print(t.p) # Cached Get
