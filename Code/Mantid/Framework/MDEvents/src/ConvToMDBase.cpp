#include "MantidMDEvents/ConvToMDBase.h"


namespace Mantid
{
  namespace MDEvents
  {

    // logger for conversion  
    Kernel::Logger& ConvToMDBase::g_Log =Kernel::Logger::get("MD-Algorithms");


    /** method which initates all main class variables
    * @param WSD        -- class describing the target workspace. 
    *                      the algorithm uses target workspace limints, transformation matix from source to the target workspace and the parameters, needed for  
    *                      unit conversion (if any) 
    * @param m_OutWSWrapper -- shared pointer to target MD Event workspace to add converted events to.
    */
    size_t  ConvToMDBase::initialize(const MDEvents::MDWSDescription &WSD, boost::shared_ptr<MDEvents::MDEventWSWrapper> inWSWrapper)
    {
      m_DetLoc = WSD.getDetectors();
      m_InWS2D = WSD.getInWS();

      // check if detector information has been precalculated:
      if(m_DetLoc)
      {
        if(!m_DetLoc->isDefined(m_InWS2D))throw(std::logic_error("Detector information has to be precalculated properly before this method is deployed"));
      }else{
        throw(std::logic_error("Detector information has to be precalculated before this method is deployed"));
      }

      // set up output MD workspace wrapper
      m_OutWSWrapper = inWSWrapper;

      // Copy ExperimentInfo (instrument, run, sample) to the output WS
      API::ExperimentInfo_sptr ei(m_InWS2D->cloneExperimentInfo());
      m_RunIndex            = m_OutWSWrapper->pWorkspace()->addExperimentInfo(ei);

      m_NDims       = m_OutWSWrapper->nDimensions();
      // allocate space for single MDEvent coordinates 
      m_Coord.resize(m_NDims);

      // retrieve the class which does the conversion of workspace data into MD WS coordinates;
      m_QConverter = MDTransfFactory::Instance().create(WSD.AlgID);


      // initialize the MD coordinates conversion class
      m_QConverter->initialize(WSD);
      // initialize units conversion which can/or can not be necessary depending on input ws/converter requested units;
      CnvrtToMD::EModes emode = WSD.getEMode();
      m_UnitConversion.initialize(WSD,m_QConverter->inputUnitID(emode,m_InWS2D));


      size_t n_spectra =m_InWS2D->getNumberHistograms();

      // get property which controls multithreaded run. If present, this property describes number of threads (or one) deployed to run conversion
      // (this can be for debugging or other tricky reasons)
      m_NumThreads = -1;
      try
      {
        Kernel::Property *pProperty = m_InWS2D->run().getProperty("NUM_THREADS");
        Kernel::PropertyWithValue<double> *thrProperty = dynamic_cast<Kernel::PropertyWithValue<double> *>(pProperty);  
        if(thrProperty)
        {
          double nDThrheads = double(*(thrProperty));
          try
          {
            m_NumThreads = boost::lexical_cast<int>(nDThrheads);
            g_Log.information()<<"***--> Changing number of running threads to "<<m_NumThreads<<std::endl;
            if(m_NumThreads<0)
            {
                g_Log.information()<<"*  --> This will reset number of threads to number of physical cores\n ";
            }
            else if(m_NumThreads==0)
            {
                g_Log.information()<<"*  --> This will disable multithreading\n ";
            }
            else if(m_NumThreads>0)
            {
                g_Log.information()<<"*  --> Multithreading processing will launch "<<m_NumThreads<<" Threads\n";
            }
          }
          catch(...){};
        }
      }
      catch(Kernel::Exception::NotFoundError &){}
   
     
      return n_spectra;
    };  

    /** empty default constructor */
    ConvToMDBase::ConvToMDBase():m_NumThreads(-1),m_DetLoc(NULL)
    { }



  } // endNamespace MDAlgorithms
}
