project( MantidParaViewMDHWNexusReader )
include_directories( SYSTEM ${PARAVIEW_INCLUDE_DIRS} )
add_paraview_plugin( MantidParaViewMDHWNexusReaderSMPlugin "1.0"
	SERVER_MANAGER_XML MDHWNexusReader.xml
	SERVER_MANAGER_SOURCES vtkMDHWNexusReader.cxx
)
set_pvplugin_properties (MantidParaViewMDHWNexusReaderSMPlugin QT_VERSION 4)

include_directories ( SYSTEM ${QWT5_INCLUDE_DIR} )

target_link_libraries( MantidParaViewMDHWNexusReaderSMPlugin LINK_PRIVATE ${TCMALLOC_LIBRARIES_LINKTIME}
${CORE_MANTIDLIBS}
DataObjects
VatesAPI
${POCO_LIBRARIES}
${Boost_LIBRARIES}
${vtkjsoncpp_LIBRARIES}
${QWT5_LIBRARIES}
Qt4::QtCore
)

if (OSX_VERSION VERSION_GREATER 10.8)
  set_target_properties(MantidParaViewMDHWNexusReaderSMPlugin PROPERTIES
                        INSTALL_RPATH "@loader_path/../../../Contents/Libraries;@loader_path/../../../Contents/MacOS")
elseif ( ${CMAKE_SYSTEM_NAME} STREQUAL "Linux" )
  set_target_properties(MantidParaViewMDHWNexusReaderSMPlugin PROPERTIES INSTALL_RPATH "\$ORIGIN/../../../${LIB_DIR}")
endif ()

install_pvplugin (MantidParaViewMDHWNexusReaderSMPlugin QT_VERSION 4)
