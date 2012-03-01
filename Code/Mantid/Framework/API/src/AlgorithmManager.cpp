//----------------------------------------------------------------------
// Includes
//----------------------------------------------------------------------
#include "MantidAPI/AlgorithmManager.h"
#include "MantidAPI/AlgorithmProxy.h"
#include "MantidKernel/ConfigService.h"

namespace Mantid
{
  namespace API
  {

    /// Private Constructor for singleton class
    AlgorithmManagerImpl::AlgorithmManagerImpl(): g_log(Kernel::Logger::get("AlgorithmManager")),m_managed_algs()
    {
      if ( ! Kernel::ConfigService::Instance().getValue("algorithms.retained",m_max_no_algs) || m_max_no_algs < 1 )
      {
        m_max_no_algs = 100; //Default to keeping 100 algorithms if not specified
      }
      
      g_log.debug() << "Algorithm Manager created." << std::endl;
    }

    /** Private destructor
    *  Prevents client from calling 'delete' on the pointer handed 
    *  out by Instance
    */
    AlgorithmManagerImpl::~AlgorithmManagerImpl()
    {
      //std::cerr << "Algorithm Manager destroyed." << std::endl;
    }

    /** Creates an instance of an algorithm, but does not own that instance
    * 
    *  @param  algName The name of the algorithm required
    *  @param  version The version of the algorithm required, if not defined most recent version is used -> version =-1
    *  @return A pointer to the created algorithm
    *  @throw  NotFoundError Thrown if algorithm requested is not registered
    */
    Algorithm_sptr AlgorithmManagerImpl::createUnmanaged(const std::string& algName,const int& version) const
    {
        return AlgorithmFactory::Instance().create(algName,version);                // Throws on fail:
    }

    /** Gets the names and categories of all the currently available algorithms
    *
    *  @return A vector of pairs of algorithm names and categories
    */
    const std::vector<std::pair<std::string,std::string> > 
      AlgorithmManagerImpl::getNamesAndCategories() const
    {
      std::vector<std::pair<std::string,std::string> > retVector;

      for (unsigned int i=0; i < m_managed_algs.size(); ++i)
      {
        std::pair<std::string,std::string> alg(m_managed_algs[i]->name(),m_managed_algs[i]->category());
        retVector.push_back(alg);
      }

      return retVector;
    }

    /** Creates and initialises an instance of an algorithm.
     *
     * The algorithm gets tracked in the list of "managed" algorithms,
     * which is shown in GUI for cancelling, etc.
     *
     * @param  algName :: The name of the algorithm required
     * @param  version :: The version of the algorithm required, if not defined most recent version is used -> version =-1
     * @param  makeProxy :: If true (default), create and return AlgorithmProxy of the given algorithm.
     *         DO NOT SET TO FALSE unless you are really sure of what you are doing!
     * @return A pointer to the created algorithm
     * @throw  NotFoundError Thrown if algorithm requested is not registered
     * @throw  std::runtime_error Thrown if properties string is ill-formed
    */
    IAlgorithm_sptr AlgorithmManagerImpl::create(const std::string& algName, const int& version, bool makeProxy)
    {
      IAlgorithm_sptr alg;
      try
      {
        Algorithm_sptr unmanagedAlg = AlgorithmFactory::Instance().create(algName,version);// Throws on fail:
        if (makeProxy)
          alg = IAlgorithm_sptr(new AlgorithmProxy(unmanagedAlg));
        else
          alg = unmanagedAlg;

        // Add to list of managed ones
        m_managed_algs.push_back(alg);
        alg->initialize();
        
        // If this takes us beyond the maximum size, then remove the oldest one(s)
        while (m_managed_algs.size() > static_cast<std::deque<IAlgorithm_sptr>::size_type>(m_max_no_algs) )
        {
          // Don't delete any algorithms that are still running.
          if (!m_managed_algs.front()->isRunning())
          {
            std::cout << "Popping out oldest algorithm " << m_managed_algs.front()->name() << std::endl;
            g_log.debug() << "Popping out oldest algorithm " << m_managed_algs.front()->name() << std::endl;
            m_managed_algs.pop_front();
            // TODO: remove the second-oldest one
          }
          else
          {
            std::cout << "NOT Popping out oldest algorithm " << m_managed_algs.front()->name() << std::endl;
            g_log.debug() << "Oldest algorithm " << m_managed_algs.front()->name() << " is running. Not popping. "
                << m_managed_algs.size() << " in queue." << std::endl;
            break;
          }

        }
      }
      catch(std::runtime_error& ex)
      {
        g_log.error()<<"AlgorithmManager:: Unable to create algorithm "<< algName << ' ' << ex.what() << std::endl;
        throw std::runtime_error("AlgorithmManager:: Unable to create algorithm " + algName + ' ' + ex.what());
      }
      return alg;
    }

    /** 
     * Clears all managed algorithm objects.
     */
    void AlgorithmManagerImpl::clear()
    {
      m_managed_algs.clear();
      return;
    }

    /**
     * Returns a shared pointer by algorithm id
     * @param id :: The ID of the algorithm
     * @returns A shared pointer tot eh algorithm
     */
    IAlgorithm_sptr AlgorithmManagerImpl::getAlgorithm(AlgorithmID id) const
    {
      for( std::deque<IAlgorithm_sptr>::const_iterator a = m_managed_algs.begin();a!=m_managed_algs.end();++a)
      {
        if ((**a).getAlgorithmID() == id) return *a;
      }
      return IAlgorithm_sptr();
    }


    /** Called by an algorithm that is executing asynchronously
     * This sends out the notification.
     *
     * @param id :: ID of the algorithm being started
     */
    void AlgorithmManagerImpl::notifyAlgorithmStarting(AlgorithmID id)
    {
      IAlgorithm_sptr alg = this->getAlgorithm(id);
      if (!alg) return;
      notificationCenter.postNotification(new AlgorithmStartingNotification(alg));
    }

  } // namespace API
} // namespace Mantid
