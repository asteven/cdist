#!/bin/sh

output_if_debug() {
   if [ "$__debug" = "yes" ]; then
      cat
   fi
}

# download a stage tarball from tftp
fetch_tftp() {
   local uri="$1"
   local target="$2"

   uri=$(echo "${uri}" | sed -e 's|^tftp://||')
   host=$(echo "${uri}" | cut -d / -f 1)
   path=$(echo "${uri}" | cut -d / -f 2-)
   tftp -g -r "${path}" -l "${target}" "${host}" || die "could not fetch ${uri}"
}
