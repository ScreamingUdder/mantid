#ifndef CROSSCORRELATETEST_H_
#define CROSSCORRELATETEST_H_

#include <cxxtest/TestSuite.h>

#include "MantidHistogramData/LinearGenerator.h"
#include "MantidAPI/AnalysisDataService.h"
#include "MantidDataObjects/Workspace2D.h"
#include "MantidAlgorithms/CrossCorrelate.h"
#include "MantidTestHelpers/WorkspaceCreationHelper.h"

using namespace Mantid;
using namespace Mantid::Algorithms;
using namespace Mantid::API;
using namespace Mantid::DataObjects;
using Mantid::HistogramData::BinEdges;
using Mantid::HistogramData::Counts;
using Mantid::HistogramData::CountStandardDeviations;

class CrossCorrelateTest : public CxxTest::TestSuite {
private:
  void makeFakeWorkspace(const std::string &name) {
    int xlen = 11;
    int nHist = 2;
    BinEdges x1(xlen, HistogramData::LinearGenerator(0.0, 0.5));
    CountStandardDeviations e1(xlen - 1, sqrt(3.0));

    Workspace2D_sptr ws = createWorkspace<Workspace2D>(nHist, xlen, xlen - 1);
    ws->getAxis(0)->setUnit("dSpacing");

    for (int i = 0; i < nHist; i++) {
      ws->setBinEdges(i, x1);
      ws->dataY(i) = {0.32, 0.47, 1.31, 3.90, 8.05,
                      10.3, 8.05, 3.9,  1.31, 0.47};
      ws->setCountStandardDeviations(i, e1);

      // offset the next spectrum
      x1 += 0.5;
    }

    AnalysisDataService::Instance().add(name, ws);
  }

public:
  void testCrossCorrelate() {
    // setup
    std::string name("CrossCorrelate");
    makeFakeWorkspace(name);
    Workspace2D_sptr ws =
        AnalysisDataService::Instance().retrieveWS<Workspace2D>(name);
    size_t nHist = ws->getNumberHistograms();

    CrossCorrelate alg;
    alg.initialize();
    alg.setProperty("InputWorkspace", name);
    alg.setProperty("OutputWorkspace", name);
    alg.setProperty("ReferenceSpectra", 0);
    alg.setProperty("WorkspaceIndexMin", 0);
    alg.setProperty("WorkspaceIndexMax", 1);
    alg.setProperty("XMin", 2.0);
    alg.setProperty("XMax", 4.0);

    TS_ASSERT_THROWS_NOTHING(alg.execute());
    TS_ASSERT(alg.isExecuted());

    // verify the output workspace
    ws = AnalysisDataService::Instance().retrieveWS<Workspace2D>(name);
    TS_ASSERT_EQUALS(nHist,
                     ws->getNumberHistograms()); // shouldn't drop histograms

    AnalysisDataService::Instance().remove(name);
  }

  void testShortRegion() {
    // setup
    std::string name("CrossCorrelate");
    makeFakeWorkspace(name);
    Workspace2D_sptr ws =
        AnalysisDataService::Instance().retrieveWS<Workspace2D>(name);
    size_t nHist = ws->getNumberHistograms();

    CrossCorrelate alg;
    alg.initialize();
    alg.setProperty("InputWorkspace", name);
    alg.setProperty("OutputWorkspace", name);
    alg.setProperty("ReferenceSpectra", 0);
    alg.setProperty("WorkspaceIndexMin", 0);
    alg.setProperty("WorkspaceIndexMax", 1);
    alg.setProperty("XMin", 2.0);
    alg.setProperty("XMax", 3.5);

    TS_ASSERT_THROWS_NOTHING(alg.execute());
    TS_ASSERT(alg.isExecuted());

    // verify the output workspace
    ws = AnalysisDataService::Instance().retrieveWS<Workspace2D>(name);
    TS_ASSERT_EQUALS(nHist,
                     ws->getNumberHistograms()); // shouldn't drop histograms

    AnalysisDataService::Instance().remove(name);
  }

  void testRegionTooShort() {
    // setup
    std::string name("CrossCorrelate");
    makeFakeWorkspace(name);
    Workspace2D_sptr ws =
        AnalysisDataService::Instance().retrieveWS<Workspace2D>(name);
    size_t nHist = ws->getNumberHistograms();

    CrossCorrelate alg;
    alg.initialize();
    alg.setProperty("InputWorkspace", name);
    alg.setProperty("OutputWorkspace", name);
    alg.setProperty("ReferenceSpectra", 0);
    alg.setProperty("WorkspaceIndexMin", 0);
    alg.setProperty("WorkspaceIndexMax", 1);
    alg.setProperty("XMin", 2.0);
    alg.setProperty("XMax", 3.0);

    /// @todo Currently this test fails - it throws a logic error
    /// because it tries to create a vector of length npoints=-1. It
    /// should probably check the range and throw a runtime error,
    /// unless the range calculation is wrong (it is exclusive of
    /// xmin)
    TS_ASSERT_THROWS_NOTHING(alg.execute());
    TS_ASSERT(alg.isExecuted());

    AnalysisDataService::Instance().remove(name);
  }
};

#endif /*CROSSCORRELATETEST_H_*/
