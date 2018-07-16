# RIFT_IO_STANDARD_CMAKE_COPYRIGHT_HEADER(BEGIN)
# Author(s): Austin Cormier
# Creation Date: 1/11/2015
# RIFT_IO_STANDARD_CMAKE_COPYRIGHT_HEADER(END)

install(
  PROGRAMS
    openmano
    openmano_cleanup.sh
  DESTINATION usr/bin
  COMPONENT ${INSTALL_COMPONENT}
)
