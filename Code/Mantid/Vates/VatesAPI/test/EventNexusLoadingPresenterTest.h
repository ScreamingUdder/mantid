#ifndef EVENT_NEXUS_LOADING_PRESENTER_TEST_H_
#define EVENT_NEXUS_LOADING_PRESENTER_TEST_H_

#include <cxxtest/TestSuite.h>
#include <vtkUnstructuredGrid.h>

#include <gmock/gmock.h>
#include <gtest/gtest.h>
#include "MockObjects.h"

#include "MantidAPI/FileFinder.h"
#include "MantidVatesAPI/EventNexusLoadingPresenter.h"

using namespace Mantid::VATES;
using namespace testing;
//=====================================================================================
// Functional tests
//=====================================================================================
class EventNexusLoadingPresenterTest : public CxxTest::TestSuite
{

private:

  // Helper method to return the full path to a real nexus file that is the correct format for this functionality.
  static std::string getSuitableFile()
  {
    return Mantid::API::FileFinder::Instance().getFullPath("CNCS_7860_event.nxs");
  }
  
  // Helper method to return the full path to a real nexus file that is the wrong format for this functionality.
  static std::string getUnhandledFile()
  {
    return Mantid::API::FileFinder::Instance().getFullPath("emu00006473.nxs");
  }

public:

void testConstructWithEmptyFileThrows()
{
  MockMDLoadingView view;

  TSM_ASSERT_THROWS("Should throw if an empty file string is given.", EventNexusLoadingPresenter<MockMDLoadingView>(&view, ""), std::invalid_argument);
}

void testConstructWithNullViewThrows()
{
  MockMDLoadingView*  pView = NULL;

  TSM_ASSERT_THROWS("Should throw if an empty file string is given.", EventNexusLoadingPresenter<MockMDLoadingView>(pView, "some_file"), std::invalid_argument);
}

void testConstructWithWrongFileTypeThrows()
{
  MockMDLoadingView view;

  TSM_ASSERT_THROWS("Should throw if an empty file string is given.", EventNexusLoadingPresenter<MockMDLoadingView>(&view, getUnhandledFile()), std::logic_error);
}

void testConstruct()
{
  MockMDLoadingView view;

  TSM_ASSERT_THROWS_NOTHING("Object should be created without exception.", EventNexusLoadingPresenter<MockMDLoadingView>(&view, getSuitableFile()));
}

void testExecution()
{
  //Setup view
  MockMDLoadingView view;
  EXPECT_CALL(view, getRecursionDepth()).Times(1); 
  EXPECT_CALL(view, getLoadInMemory()).WillOnce(testing::Return(true)); 
  EXPECT_CALL(view, updateAlgorithmProgress(_)).Times(AnyNumber());

  //Setup rendering factory
  MockvtkDataSetFactory factory;
  EXPECT_CALL(factory, initialize(_)).Times(1);
  EXPECT_CALL(factory, create()).WillOnce(testing::Return(vtkUnstructuredGrid::New()));
  EXPECT_CALL(factory, setRecursionDepth(_)).Times(1);

  //Setup progress updates object
  FilterUpdateProgressAction<MockMDLoadingView> progressAction(&view);

  //Create the presenter and runit!
  EventNexusLoadingPresenter<MockMDLoadingView> presenter(&view, getSuitableFile());
  vtkDataSet* product = presenter.execute(&factory, progressAction);

  TSM_ASSERT("Should have generated a vtkDataSet", NULL != product);
  TSM_ASSERT_EQUALS("Wrong type of output generated", "vtkUnstructuredGrid", std::string(product->GetClassName()));
  TSM_ASSERT("No field data!", NULL != product->GetFieldData());
  TSM_ASSERT_EQUALS("One array expected on field data!", 1, product->GetFieldData()->GetNumberOfArrays());
  TS_ASSERT_THROWS_NOTHING(presenter.hasTDimensionAvailable());
  TS_ASSERT_THROWS_NOTHING(presenter.getGeometryXML());

  TS_ASSERT(Mock::VerifyAndClearExpectations(&view));
  TS_ASSERT(Mock::VerifyAndClearExpectations(&factory));

  product->Delete();
}

void testCallHasTDimThrows()
{
  MockMDLoadingView view;
  EventNexusLoadingPresenter<MockMDLoadingView> presenter(&view, getSuitableFile());
  TSM_ASSERT_THROWS("Should throw. Execute not yet run.", presenter.hasTDimensionAvailable(), std::runtime_error);
}

void testCallGetTDimensionValuesThrows()
{
  MockMDLoadingView view;
  EventNexusLoadingPresenter<MockMDLoadingView> presenter(&view, getSuitableFile());
  TSM_ASSERT_THROWS("Should throw. Execute not yet run.", presenter.getTimeStepValues(), std::runtime_error);
}

void testCallGetGeometryThrows()
{
  MockMDLoadingView view;
  EventNexusLoadingPresenter<MockMDLoadingView> presenter(&view, getSuitableFile());
  TSM_ASSERT_THROWS("Should throw. Execute not yet run.", presenter.getGeometryXML(), std::runtime_error);
}

};
#endif