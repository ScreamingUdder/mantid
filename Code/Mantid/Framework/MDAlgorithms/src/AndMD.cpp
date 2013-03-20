/*WIKI*

Perform the And boolean operation on two MDHistoWorkspaces.
The & operation is performed element-by-element.
A signal of 0.0 means "false" and any non-zero signal is "true".

*WIKI*/
/*WIKI_USAGE*

 C = A & B
 A &= B

See [[MDHistoWorkspace#Boolean_Operations|this page]] for examples on using boolean operations.

*WIKI_USAGE*/

#include "MantidMDAlgorithms/AndMD.h"
#include "MantidKernel/System.h"

using namespace Mantid::Kernel;
using namespace Mantid::API;

namespace Mantid
{
namespace MDAlgorithms
{

  // Register the algorithm into the AlgorithmFactory
  DECLARE_ALGORITHM(AndMD)
  
  //----------------------------------------------------------------------------------------------
  /** Constructor
   */
  AndMD::AndMD()
  {  }
    
  //----------------------------------------------------------------------------------------------
  /** Destructor
   */
  AndMD::~AndMD()
  {  }
  
  //----------------------------------------------------------------------------------------------
  /// Algorithm's name for identification. @see Algorithm::name
  const std::string AndMD::name() const { return "AndMD";};
  
  /// Algorithm's version for identification. @see Algorithm::version
  int AndMD::version() const { return 1;};
  
  //----------------------------------------------------------------------------------------------
  /// Run the algorithm with a MDHisotWorkspace as output and operand
  void AndMD::execHistoHisto(Mantid::MDEvents::MDHistoWorkspace_sptr out, Mantid::MDEvents::MDHistoWorkspace_const_sptr operand)
  {
    out->operator &=(*operand);
  }


} // namespace Mantid
} // namespace MDAlgorithms
