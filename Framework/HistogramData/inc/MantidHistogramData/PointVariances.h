#ifndef MANTID_HISTOGRAMDATA_POINTVARIANCES_H_
#define MANTID_HISTOGRAMDATA_POINTVARIANCES_H_

#include "MantidHistogramData/DllConfig.h"
#include "MantidHistogramData/VarianceVectorOf.h"
#include "MantidHistogramData/HistogramDx.h"

namespace Mantid {
namespace HistogramData {

class BinEdgeVariances;
class PointStandardDeviations;

/** PointVariances : TODO: DESCRIPTION

  Copyright &copy; 2016 ISIS Rutherford Appleton Laboratory, NScD Oak Ridge
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

  File change history is stored at: <https://github.com/mantidproject/mantid>
  Code Documentation is available at: <http://doxygen.mantidproject.org>
*/
class MANTID_HISTOGRAMDATA_DLL PointVariances
    : public detail::VarianceVectorOf<PointVariances, HistogramDx,
                                      PointStandardDeviations> {
public:
  using VarianceVectorOf<PointVariances, HistogramDx,
                         PointStandardDeviations>::VarianceVectorOf;
  using VarianceVectorOf<PointVariances, HistogramDx, PointStandardDeviations>::
  operator=;
  PointVariances() = default;
  // The copy and move constructor and assignment are not captured properly by
  // the using declaration above, so we need them here explicitly.
  PointVariances(const PointVariances &) = default;
  PointVariances(PointVariances &&) = default;
  PointVariances &operator=(const PointVariances &)& = default;
  PointVariances &operator=(PointVariances &&)& = default;

  /// Constructs PointVariances from BinEdgeVariances, where each point is a bin
  /// center.
  PointVariances(const BinEdgeVariances &edges);
};

} // namespace HistogramData
} // namespace Mantid

#endif /* MANTID_HISTOGRAMDATA_POINTVARIANCES_H_ */