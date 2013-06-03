#
# 2013 Nico Schottelius (nico-cdist at schottelius.org)
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

DIST=dist-tag dist-branch-merge dist-pypi dist-archlinux-makepkg
RELEASE=web release-man pub 
RELEASE+=release-blog release-ml
RELEASE+=dist-freecode dist-manual dist-archlinux-aur-upload

version:

$(DIST): dist-check
$(RELEASE): $(DIST)

man: mangen mantype manbuild

dist: $(DIST)
	echo "Run \"make release\" to release to the public"

release: $(RELEASE)

dist-archlinux: dist-pypi

dist-check: clean man

dist-archlinux-makepkg: PKGBUILD
	makepkg -c --source

release-pub: man

PKGBUILD: PKGBUILD.in
	./PKGBUILD.in

%:
	./build-helper $@
