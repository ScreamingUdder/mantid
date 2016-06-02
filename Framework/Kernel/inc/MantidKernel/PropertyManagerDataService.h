#ifndef MANTID_KERNEL_PROPERTYMANAGERDATASERVICE_
#define MANTID_KERNEL_PROPERTYMANAGERDATASERVICE_

#include "MantidKernel/DataService.h"
#include "MantidKernel/PropertyManager.h"
#include "MantidKernel/SingletonHolder.h"

namespace Mantid {
namespace Kernel {
/**
PropertyManagerDataService Class. Derived from DataService.

Copyright &copy; 2012 ISIS Rutherford Appleton Laboratory, NScD Oak Ridge
National Laboratory & European Spallation Source

This file is part of Mantid.

Mantid is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or
(at your option) any later version.

Mantid is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

File change history is stored at: <https://github.com/mantidproject/mantid>.
Code Documentation is available at: <http://doxygen.mantidproject.org>
*/
class MANTID_KERNEL_DLL PropertyManagerDataServiceImpl final
    : public DataService<PropertyManager> {
public:
  PropertyManagerDataServiceImpl(const PropertyManagerDataServiceImpl &) =
      delete;
  PropertyManagerDataServiceImpl &
  operator=(const PropertyManagerDataServiceImpl &) = delete;

private:
  friend struct Mantid::Kernel::CreateUsingNew<PropertyManagerDataServiceImpl>;
  /// Constructor
  PropertyManagerDataServiceImpl();
  ~PropertyManagerDataServiceImpl() override = default;
};

/// Forward declaration of a specialisation of SingletonHolder for
/// PropertyManagerDataServiceImpl (needed for dllexport/dllimport) and a
/// typedef for it.
#ifdef _WIN32
// this breaks new namespace declaraion rules; need to find a better fix
template class MANTID_KERNEL_DLL
    Mantid::Kernel::SingletonHolder<PropertyManagerDataServiceImpl>;
#endif /* _WIN32 */
typedef  Mantid::Kernel::SingletonHolder<
    PropertyManagerDataServiceImpl> PropertyManagerDataService;

} // Namespace Kernel
} // Namespace Mantid
#endif /*MANTID_KERNEL_PROPERTYMANAGERDATASERVICE_*/
