#ifndef MANTIDGLWIDGET_H_
#define MANTIDGLWIDGET_H_

#include "MantidGeometry/IComponent.h"

#include <QGLWidget>
#include <QString>

#include <boost/shared_ptr.hpp>

class ProjectionSurface;

/**
  \class  MantidGLWidget
  \brief  OpenGL Qt Widget which renders Mantid Geometry ObjComponents
*/

class MantidGLWidget : public QGLWidget
{
  Q_OBJECT
public:
  //enum PolygonMode{ SOLID, WIREFRAME };
  MantidGLWidget(QWidget* parent=0); ///< Constructor
  virtual ~MantidGLWidget();         ///< Destructor
  void setSurface(boost::shared_ptr<ProjectionSurface> surface);
  boost::shared_ptr<ProjectionSurface> getSurface(){return m_surface;}
  
  void setBackgroundColor(QColor);
  QColor currentBackgroundColor() const;
  void saveToFile(const QString & filename);
  int getLightingState() const {return m_lightingState;}

signals:
  void mouseOut();

public slots:
  void enableLighting(bool);
  //void setWireframe(bool);
  void updateView();
  void updateDetectors();
  void componentSelected(Mantid::Geometry::ComponentID id);

protected:
  void initializeGL();
  void resetWidget();
  void MakeObject();
  void paintEvent(QPaintEvent *event);
  void resizeGL(int,int);
  void contextMenuEvent(QContextMenuEvent*);
  void mousePressEvent(QMouseEvent*);
  void mouseMoveEvent(QMouseEvent*);
  void mouseReleaseEvent(QMouseEvent*);
  void wheelEvent(QWheelEvent *);
  void keyPressEvent(QKeyEvent *);
  void keyReleaseEvent(QKeyEvent *);
  void draw();
  void checkGLError(const QString& funName);
  void leaveEvent (QEvent*);
private:
  void setRenderingOptions();

  //QColor m_bgColor;                 ///< Background color
  //PolygonMode m_polygonMode;     ///< SOLID or WIREFRAME
  int m_lightingState;           ///< 0 = light off; 2 = light on
  bool m_isKeyPressed;
  bool m_firstFrame;

  //// Surface stuff
  boost::shared_ptr<ProjectionSurface> m_surface;

};

#endif /*MANTIDGLWIDGET_H_*/

