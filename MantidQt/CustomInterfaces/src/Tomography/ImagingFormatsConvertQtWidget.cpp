#include "MantidQtCustomInterfaces/Tomography/ImagingFormatsConvertQtWidget.h"
#include "MantidAPI/MatrixWorkspace.h"
#include "MantidAPI/WorkspaceFactory.h"
#include "MantidQtAPI/AlgorithmInputHistory.h"
#include "MantidQtCustomInterfaces/Tomography/ImagingFormatsConvertPresenter.h"

using namespace Mantid::API;
using namespace MantidQt::CustomInterfaces;

#include <QCloseEvent>
#include <QFileDialog>
#include <QImageReader>
#include <QImageWriter>
#include <QMessageBox>
#include <QSettings>

#include <iostream>
#include <QImage>

namespace MantidQt {
namespace CustomInterfaces {

// this would be more like a CustomWidget if it's eventually moved there
const std::string ImagingFormatsConvertQtWidget::m_settingsGroup =
    "CustomInterfaces/ImagingFormatsConvertView";

ImagingFormatsConvertQtWidget::ImagingFormatsConvertQtWidget(QWidget *parent)
    : QWidget(parent), IImagingFormatsConvertView(), m_presenter(nullptr) {
  initLayout();
}

void ImagingFormatsConvertQtWidget::userWarning(
    const std::string &warn, const std::string &description) {
  QMessageBox::warning(this, QString::fromStdString(warn),
                       QString::fromStdString(description), QMessageBox::Ok,
                       QMessageBox::Ok);
}

void ImagingFormatsConvertQtWidget::userError(const std::string &err,
                                              const std::string &description) {
  QMessageBox::critical(this, QString::fromStdString(err),
                        QString::fromStdString(description), QMessageBox::Ok,
                        QMessageBox::Ok);
}

void ImagingFormatsConvertQtWidget::setFormats(
    const std::vector<std::string> &fmts, const std::vector<bool> &enable) {
  // same formats for inputs and outputs
  setFormatsCombo(m_ui.comboBox_input_format, fmts, enable);
  setFormatsCombo(m_ui.comboBox_output_format, fmts, enable);

  m_ui.spinBox_max_search_depth->setValue(3);
  if (m_ui.comboBox_output_format->count() > 0) {
    m_ui.comboBox_output_format->setCurrentIndex(1);
  }
}

void ImagingFormatsConvertQtWidget::setFormatsCombo(
    QComboBox *cbox, const std::vector<std::string> &fmts,
    const std::vector<bool> &enable) {
  cbox->clear();
  for (const auto &name : fmts) {
    cbox->addItem(QString::fromStdString(name));
  }

  if (enable.empty() || enable.size() != fmts.size())
    return;

  // disable
}

std::string ImagingFormatsConvertQtWidget::inputPath() const {
  return m_ui.lineEdit_input_path->text().toStdString();
}

std::string ImagingFormatsConvertQtWidget::inputFormatName() const {
  const auto cbox = m_ui.comboBox_input_format;
  if (!cbox)
    return "";

  return cbox->currentText().toStdString();
}

std::string ImagingFormatsConvertQtWidget::outputPath() const {
  return m_ui.lineEdit_output_path->text().toStdString();
}

std::string ImagingFormatsConvertQtWidget::outputFormatName() const {
  const auto cbox = m_ui.comboBox_output_format;
  if (!cbox)
    return "";

  return cbox->currentText().toStdString();
}

bool ImagingFormatsConvertQtWidget::compressHint() const {
  return 0 == m_ui.comboBox_compression->currentIndex();
}

void ImagingFormatsConvertQtWidget::convert(
    const std::string &inputName, const std::string &inputFormat,
    const std::string &outputName, const std::string &outputFormat) const {

  // Simpler load with QImage: img.load(QString::fromStdString(inputName));
  QImageReader reader(inputName.c_str());
  if (!reader.autoDetectImageFormat()) {
    reader.setFormat(inputFormat.c_str());
  }
  QImage img = reader.read();

  if (!img.isGrayscale()) {
    // Qt5 has QImage::Format_Alpha8;
    QImage::Format toFormat = QImage::Format_RGB32;
    Qt::ImageConversionFlag toFlags = Qt::MonoOnly;
    img.convertToFormat(toFormat, toFlags);
  }

  // With (less flexible) QImage: img.save(QString::fromStdString(outputName));
  QImageWriter writer(QString::fromStdString(outputName));
  writer.setFormat(outputFormat.c_str());
  if (compressHint())
    writer.setCompression(1);
  writer.write(img);
}

void ImagingFormatsConvertQtWidget::writeImg(
    MatrixWorkspace_sptr inWks, const std::string &outputName,
    const std::string &outFormat) const {

  size_t width = inWks->getNumberHistograms();
  if (0 == width)
    return;
  size_t height = inWks->blocksize();
  QImage img(QSize(static_cast<int>(width), static_cast<int>(height)),
             QImage::Format_Indexed8);

  int tableSize = 256;
  QVector<QRgb> grayscale;
  grayscale.resize(tableSize);
  for (int i = 0; i < grayscale.size(); i++) {
    grayscale.push_back(qRgb(i, i, i));
  }
  const double scaleFactor = std::numeric_limits<unsigned char>::max();
  for (int yi = 0; yi < static_cast<int>(width); ++yi) {
    const auto &row = inWks->readY(yi);
    for (int xi = 0; xi < static_cast<int>(width); ++xi) {
      const int scaled = static_cast<int>(row[xi] / scaleFactor);
      QRgb vRgb = qRgb(scaled, scaled, scaled);
      img.setPixel(xi, yi, vRgb);
    }
  }

  QImageWriter writer(QString::fromStdString(outputName));
  writer.setFormat(outFormat.c_str());
  if (compressHint())
    writer.setCompression(1);
  writer.write(img);
}

MatrixWorkspace_sptr
ImagingFormatsConvertQtWidget::loadImg(const std::string &inputName,
                                       const std::string &inFormat) const {
  QImageReader reader(inputName.c_str());
  if (!reader.autoDetectImageFormat()) {
    reader.setFormat(inFormat.c_str());
  }

  int width = reader.size().width();
  int height = reader.size().height();
  QImage img = reader.read();

  MatrixWorkspace_sptr imgWks = boost::dynamic_pointer_cast<MatrixWorkspace>(
      WorkspaceFactory::Instance().create("Workspace2D", height, width + 1,
                                          width));
  imgWks->setTitle(inputName);
  const double scaleFactor = std::numeric_limits<unsigned char>::max();
  for (int yi = 0; yi < static_cast<int>(width); ++yi) {
    const auto &row = imgWks->getSpectrum(yi);
    auto &dataY = row->dataY();
    auto &dataX = row->dataX();
    std::fill(dataX.begin(), dataX.end(), static_cast<double>(yi));
    for (int xi = 0; xi < static_cast<int>(width); ++xi) {
      QRgb vRgb = img.pixel(xi, yi);
      dataY[xi] = scaleFactor * qGray(vRgb);
    }
  }

  return imgWks;
}

size_t ImagingFormatsConvertQtWidget::maxSearchDepth() const {
  return static_cast<size_t>(m_ui.spinBox_max_search_depth->value());
}

void ImagingFormatsConvertQtWidget::initLayout() {
  // setup container ui
  m_ui.setupUi(this);

  readSettings();

  setup();
  // presenter that knows how to handle a view like this. It should
  // take care of all the logic. Note the view needs to now the
  // concrete presenter here
  m_presenter.reset(new ImagingFormatsConvertPresenter(this));

  // it will know what compute resources and tools we have available:
  // This view doesn't even know the names of compute resources, etc.
  m_presenter->notify(IImagingFormatsConvertPresenter::Init);
}

void ImagingFormatsConvertQtWidget::setup() {

  connect(m_ui.pushButton_browse_input, SIGNAL(released()), this,
          SLOT(browseImgInputConvertClicked()));

  connect(m_ui.pushButton_browse_output, SIGNAL(released()), this,
          SLOT(browseImgOutputConvertClicked()));

  connect(m_ui.pushButton_convert, SIGNAL(released()), this,
          SLOT(convertClicked()));
}

void ImagingFormatsConvertQtWidget::readSettings() {
  QSettings qs;
  qs.beginGroup(QString::fromStdString(m_settingsGroup));

  m_ui.comboBox_input_format->setCurrentIndex(
      qs.value("input-format", 0).toInt());
  m_ui.lineEdit_input_path->setText(qs.value("input-path", "").toString());

  m_ui.comboBox_output_format->setCurrentIndex(
      qs.value("output-format", 0).toInt());
  m_ui.comboBox_bit_depth->setCurrentIndex(qs.value("bit-depth", 0).toInt());
  m_ui.comboBox_compression->setCurrentIndex(
      qs.value("compression", 0).toInt());
  m_ui.spinBox_max_search_depth->setValue(
      qs.value("max-search-depth", 0).toInt());
  m_ui.lineEdit_output_path->setText(qs.value("output-path", "").toString());

  restoreGeometry(qs.value("interface-win-geometry").toByteArray());
  qs.endGroup();
}

void ImagingFormatsConvertQtWidget::saveSettings() const {
  QSettings qs;
  qs.beginGroup(QString::fromStdString(m_settingsGroup));

  qs.setValue("input-format", m_ui.comboBox_input_format->currentIndex());
  qs.setValue("input-path", m_ui.lineEdit_input_path->text());

  qs.setValue("output-format", m_ui.comboBox_output_format->currentIndex());
  qs.setValue("bit-depth", m_ui.comboBox_bit_depth->currentIndex());
  qs.setValue("compression", m_ui.comboBox_compression->currentIndex());
  qs.setValue("max-search-depth", m_ui.spinBox_max_search_depth->value());
  qs.setValue("output-path", m_ui.lineEdit_output_path->text());

  qs.setValue("interface-win-geometry", saveGeometry());
  qs.endGroup();
}

void ImagingFormatsConvertQtWidget::browseImgInputConvertClicked() {
  grabUserBrowseDir(m_ui.lineEdit_input_path);
}

void ImagingFormatsConvertQtWidget::browseImgOutputConvertClicked() {
  grabUserBrowseDir(m_ui.lineEdit_output_path);
}

void ImagingFormatsConvertQtWidget::convertClicked() {
  m_presenter->notify(IImagingFormatsConvertPresenter::Convert);
}

std::string ImagingFormatsConvertQtWidget::grabUserBrowseDir(
    QLineEdit *le, const std::string &userMsg, bool remember) {

  QString prev;
  if (le->text().isEmpty()) {
    prev =
        MantidQt::API::AlgorithmInputHistory::Instance().getPreviousDirectory();
  } else {
    prev = le->text();
  }

  QString path(QFileDialog::getExistingDirectory(
      this, tr(QString::fromStdString(userMsg)), prev));

  if (!path.isEmpty()) {
    le->setText(path);
    if (remember) {
      MantidQt::API::AlgorithmInputHistory::Instance().setPreviousDirectory(
          path);
    }
  }

  return path.toStdString();
}

std::string ImagingFormatsConvertQtWidget::askImgOrStackPath() {
  // get path
  QString fitsStr = QString("Supported formats: FITS, TIFF and PNG "
                            "(*.fits *.fit *.tiff *.tif *.png);;"
                            "FITS, Flexible Image Transport System images "
                            "(*.fits *.fit);;"
                            "TIFF, Tagged Image File Format "
                            "(*.tif *.tiff);;"
                            "PNG, Portable Network Graphics "
                            "(*.png);;"
                            "Other extensions/all files (*.*)");
  QString prevPath =
      MantidQt::API::AlgorithmInputHistory::Instance().getPreviousDirectory();
  QString path(QFileDialog::getExistingDirectory(
      this, tr("Open stack of images"), prevPath, QFileDialog::ShowDirsOnly));
  if (!path.isEmpty()) {
    MantidQt::API::AlgorithmInputHistory::Instance().setPreviousDirectory(path);
  }

  return path.toStdString();
}

void ImagingFormatsConvertQtWidget::closeEvent(QCloseEvent *event) {
  m_presenter->notify(IImagingFormatsConvertPresenter::ShutDown);
  event->accept();
}

} // namespace CustomInterfaces
} // namespace MantidQt
