# -*- coding: utf-8 -*-
#
# 2011 Steven Armstrong (steven-cdist at armstrong.cc)
# 2011 Nico Schottelius (nico-cdist at schottelius.org)
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
import os
import collections

import cdist
import cdist.core
from cdist.util import fsproperty

log = logging.getLogger(__name__)

OBJECT_MARKER = '.object'


class IllegalObjectIdError(cdist.Error):
    def __init__(self, object_id, message=None):
        self.object_id = object_id
        self.message = message or 'Illegal object id'

    def __str__(self):
        return '%s: %s' % (self.message, self.object_id)


class Object(object):
    """Represents a cdist object.

    All interaction with objects in cdist should be done through this class.
    Directly accessing an object through the file system from python code is
    a bug.

    """

    # Constants for use with Object.state
    STATE_PREPARED = "prepared"
    STATE_RUNNING = "running"
    STATE_DONE = "done"

    @classmethod
    def list_objects(cls, object_base_path, type_base_path):
        """Return a list of object instances"""
        for object_name in cls.list_object_names(object_base_path):
            type_name, object_id = cls.split_name(object_name)
            yield cls(cdist.core.Type(type_base_path, type_name), object_base_path, object_id=object_id)

    @classmethod
    def list_type_names(cls, object_base_path):
        """Return a list of type names"""
        for path, dirs, files in os.walk(object_base_path):
            if cdist.core.TYPE_MARKER in files:
                name = cdist.core.Type.name_from_path(
                    os.path.relpath(path, object_base_path)
                )
                yield name

    @classmethod
    def list_object_names(cls, object_base_path):
        """Return a list of object names"""
        for path, dirs, files in os.walk(object_base_path):
            if cdist.core.TYPE_MARKER in files:
                type_name = cdist.core.Type.name_from_path(
                    os.path.relpath(path, object_base_path)
                )
                type_path = path
            if OBJECT_MARKER in dirs:
                # don't visit .object directories
                dirs.remove(OBJECT_MARKER)
                object_id = os.path.relpath(path, type_path)
                yield cls.join_name(type_name, object_id)

    @staticmethod
    def split_name(object_name):
        """split_name('__type_name/the/object_id') -> ('__type_name', 'the/object_id')

        Split the given object name into it's type and object_id parts.

        """
        type_name = object_name.split(os.sep)[0]
        # FIXME: allow object without object_id? e.g. for singleton
        object_id = os.sep.join(object_name.split(os.sep)[1:])
        return type_name, object_id

    @staticmethod
    def join_name(type_name, object_id):
        """join_name('__type_name', 'the/object_id') -> __type_name/the/object_id'

        Join the given type_name and object_id into an object name.

        """
        return os.path.join(type_name, object_id)

    def __init__(self, cdist_type, base_path, object_id=None):
        if object_id:
            if object_id.startswith('/'):
                raise IllegalObjectIdError(object_id, 'object_id may not start with /')
            if OBJECT_MARKER in object_id:
                raise IllegalObjectIdError(object_id, 'object_id may not contain \'%s\'' % OBJECT_MARKER)
        self.type = cdist_type # instance of Type
        self.base_path = base_path
        self.object_id = object_id
        self.name = self.join_name(self.type.name, self.object_id)
        self.path = os.path.join(self.type.path, self.object_id, OBJECT_MARKER)
        self.absolute_path = os.path.join(self.base_path, self.path)
        self.code_local_path = os.path.join(self.path, "code-local")
        self.code_remote_path = os.path.join(self.path, "code-remote")
        self.parameter_path = os.path.join(self.path, "parameter")

    def __repr__(self):
        return '<Object %s>' % self.name

    def __eq__(self, other):
        """define equality as 'attributes are the same'"""
        return self.__dict__ == other.__dict__

    def __lt__(self, other):
        return isinstance(other, self.__class__) and self.name < other.name

    def object_from_name(self, object_name):
        """Convenience method for creating an object instance from an object name.

        Mainly intended to create objects when resolving requirements.

        e.g:
            <Object __foo/bar>.object_from_name('__other/object') -> <Object __other/object>

        """
        type_path = self.type.base_path
        object_path = self.base_path
        type_name, object_id = self.split_name(object_name)
        return self.__class__(self.type.__class__(type_path, type_name), object_path, object_id=object_id)

    # FIXME: still needed?
    @property
    def explorer_path(self):
        """Create and return the relative path to this objects explorers"""
        # create absolute path
        path = os.path.join(self.absolute_path, "explorer")
        if not os.path.isdir(path):
            os.mkdir(path)
        # return relative path
        return os.path.join(self.path, "explorer")

    requirements = fsproperty.FileListProperty(lambda obj: os.path.join(obj.absolute_path, 'require'))
    parameters = fsproperty.DirectoryDictProperty(lambda obj: os.path.join(obj.base_path, obj.parameter_path))
    explorers = fsproperty.DirectoryDictProperty(lambda obj: os.path.join(obj.base_path, obj.explorer_path))
    changed = fsproperty.FileBooleanProperty(lambda obj: os.path.join(obj.absolute_path, "changed"))
    state = fsproperty.FileStringProperty(lambda obj: os.path.join(obj.absolute_path, "state"))
    source = fsproperty.FileListProperty(lambda obj: os.path.join(obj.absolute_path, "source"))
    code_local = fsproperty.FileStringProperty(lambda obj: os.path.join(obj.base_path, obj.code_local_path))
    code_remote = fsproperty.FileStringProperty(lambda obj: os.path.join(obj.base_path, obj.code_remote_path))

    @property
    def exists(self):
        """Checks wether this cdist object exists on the file systems."""
        return os.path.exists(self.absolute_path)

    def create(self):
        """Create this cdist object on the filesystem.
        """
        try:
            os.makedirs(self.absolute_path, exist_ok=False)
            absolute_parameter_path = os.path.join(self.base_path, self.parameter_path)
            os.makedirs(absolute_parameter_path, exist_ok=False)
        except EnvironmentError as error:
            raise cdist.Error('Error creating directories for cdist object: %s: %s' % (self, error))
