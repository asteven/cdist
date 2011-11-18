# -*- coding: utf-8 -*-
#
# 2011 Steven Armstrong (steven-cdist at armstrong.cc)
#
# This file is part of cdist.
#
# cdist is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# cdist is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with cdist. If not, see <http://www.gnu.org/licenses/>.
#
#

import logging
import itertools

import cdist

log = logging.getLogger(__name__)


class DependencyResolver(object):
    """Cdist's dependency resolver.

    Usage:
    resolver = DependencyResolver(list_of_objects)
    from pprint import pprint
    pprint(resolver.graph)

    for cdist_object in resolver:
        do_something_with(cdist_object)

    """
    def __init__(self, objects, logger=None):
        self.objects = objects
        self._graph = None
        self.log = logger or log

    @property
    def graph(self):
        """Build the dependency graph.

        Returns a dict where the keys are the object names and the values are
        lists of all dependencies including the key object itself.
        """
        if self._graph is None:
            graph = {}
            for o in self.objects:
                resolved = []
                unresolved = []
                self.resolve_object_dependencies(o, resolved, unresolved)
                graph[o.name] = resolved
            self._graph = graph
        return self._graph

    def resolve_object_dependencies(self, cdist_object, resolved, unresolved):
        """Resolve all dependencies for the given cdist_object and store them
        in the list which is passed as the 'resolved' arguments.

        e.g.
        resolved = []
        unresolved = []
        resolve_object_dependencies(some_object, resolved, unresolved)
        print("Dependencies for %s: %s" % (some_object, resolved))
        """
        self.log.debug('Resolving dependencies for: %s' % cdist_object.name)
        unresolved.append(cdist_object)
        for requirement in cdist_object.requirements:
            self.log.debug("Object %s requires %s", cdist_object, requirement)
            required_object = cdist_object.object_from_name(requirement)

            # The user may have created dependencies without satisfying them
            if not required_object.exists:
                raise cdist.Error(cdist_object.name + " requires non-existing " + required_object.name)

            if required_object not in resolved:
                if required_object in unresolved:
                    raise cdist.Error('Circular reference detected: %s -> %s' % (cdist_object.name, required_object.name))
                self.resolve_object_dependencies(required_object, resolved, unresolved)
        resolved.append(cdist_object)
        unresolved.remove(cdist_object)

    def __iter__(self):
        """Iterate over all unique objects while resolving dependencies.
        """
        iterable = itertools.chain(*self.graph.values())
        # Keep record of objects that have already been seen
        seen = set()
        seen_add = seen.add
        for cdist_object in itertools.filterfalse(seen.__contains__, iterable):
            seen_add(cdist_object)
            yield cdist_object
