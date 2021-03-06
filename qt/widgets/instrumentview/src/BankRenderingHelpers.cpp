#include "MantidQtWidgets/InstrumentView/BankRenderingHelpers.h"
#include "MantidGeometry/Instrument/ComponentInfo.h"
#include "MantidGeometry/Objects/IObject.h"
#include "MantidGeometry/Objects/ShapeFactory.h"
#include "MantidGeometry/Rendering/GeometryHandler.h"
#include "MantidGeometry/Rendering/OpenGL_Headers.h"
#include "MantidGeometry/Rendering/ShapeInfo.h"
#include "MantidKernel/Quat.h"

namespace {
Mantid::Kernel::Logger g_log("BankRenderingHelpers");

// Round a number up to the nearest power  of 2
size_t roundToNearestPowerOfTwo(size_t val) {
  size_t rounded = 2;
  while (val > rounded)
    rounded *= 2;
  return rounded;
}

void addVertex(const Mantid::Geometry::ComponentInfo &compInfo, size_t detIndex,
               const Mantid::Kernel::V3D &basePos, double xstep, double ystep) {
  auto pos = compInfo.position(detIndex) - basePos;
  pos += Mantid::Kernel::V3D(xstep * (+0.5), ystep * (-0.5),
                             0.0); // Adjust to account for the size of a pixel
  glVertex3f(static_cast<GLfloat>(pos.X()), static_cast<GLfloat>(pos.Y()),
             static_cast<GLfloat>(pos.Z()));
}

void setBankNormal(const Mantid::Kernel::V3D &pos1,
                   const Mantid::Kernel::V3D &pos2,
                   const Mantid::Kernel::V3D &basePos) {
  // Set the bank normal to facilitate lighting effects
  auto vec1 = pos1 - basePos;
  auto vec2 = pos2 - basePos;
  auto normal = vec1.cross_prod(vec2);
  normal.normalize();
  glNormal3f(static_cast<GLfloat>(normal.X()), static_cast<GLfloat>(normal.Y()),
             static_cast<GLfloat>(normal.Z()));
}

void extractHexahedron(const Mantid::Geometry::IObject &shape,
                       std::vector<Mantid::Kernel::V3D> &hex) {
  const auto &shapeInfo = shape.getGeometryHandler()->shapeInfo();
  const auto &points = shapeInfo.points();
  hex.assign(points.begin(), points.begin() + 4);
}

void rotateHexahedron(std::vector<Mantid::Kernel::V3D> &hex,
                      const Mantid::Kernel::Quat &rotation) {
  for (auto &pos : hex)
    rotation.rotate(pos);
}

void offsetHexahedronPosition(std::vector<Mantid::Kernel::V3D> &hex,
                              const Mantid::Kernel::V3D &offset) {
  for (auto &pos : hex)
    pos += offset;
}
} // namespace

namespace MantidQt {
namespace MantidWidgets {
namespace BankRenderingHelpers {

std::pair<size_t, size_t> getCorrectedTextureSize(const size_t width,
                                                  const size_t height) {
  return {roundToNearestPowerOfTwo(width), roundToNearestPowerOfTwo(height)};
}

void renderRectangularBank(const Mantid::Geometry::ComponentInfo &compInfo,
                           size_t index) {
  auto bank = compInfo.quadrilateralComponent(index);
  auto xstep = (compInfo.position(bank.bottomRight).X() -
                compInfo.position(bank.bottomLeft).X()) /
               static_cast<double>(bank.nX);
  auto ystep = (compInfo.position(bank.topRight).Y() -
                compInfo.position(bank.bottomLeft).Y()) /
               static_cast<double>(bank.nY);
  // Because texture colours are combined with the geometry colour
  // make sure the current colour is white
  glColor3f(1.0f, 1.0f, 1.0f);

  // Nearest-neighbor scaling
  glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
  glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
  glEnable(GL_TEXTURE_2D); // enable texture mapping

  size_t texx, texy;
  auto res = getCorrectedTextureSize(bank.nX, bank.nY);
  texx = res.first;
  texy = res.second;
  double tex_frac_x = static_cast<double>(bank.nX) / static_cast<double>(texx);
  double tex_frac_y = static_cast<double>(bank.nY) / static_cast<double>(texy);

  glBegin(GL_QUADS);

  auto basePos = compInfo.position(bank.bottomLeft);

  // Set the bank normal to facilitate lighting effects
  setBankNormal(compInfo.position(bank.bottomRight),
                compInfo.position(bank.topLeft), basePos);

  glTexCoord2f(0.0, 0.0);
  addVertex(compInfo, bank.bottomLeft, basePos, xstep, ystep);

  glTexCoord2f(static_cast<GLfloat>(tex_frac_x), 0.0);
  addVertex(compInfo, bank.bottomRight, basePos, xstep, ystep);

  glTexCoord2f(static_cast<GLfloat>(tex_frac_x),
               static_cast<GLfloat>(tex_frac_y));
  addVertex(compInfo, bank.topRight, basePos, xstep, ystep);

  glTexCoord2f(0.0, static_cast<GLfloat>(tex_frac_y));
  addVertex(compInfo, bank.topLeft, basePos, xstep, ystep);

  glEnd();

  if (glGetError() > 0)
    g_log.error() << "OpenGL error in renderRectangularBank() \n";

  glDisable(
      GL_TEXTURE_2D); // stop texture mapping - not sure if this is necessary.
}

void renderStructuredBank(const Mantid::Geometry::ComponentInfo &compInfo,
                          size_t index, const std::vector<GLColor> &color) {
  glBegin(GL_QUADS);

  const auto &columns = compInfo.children(index);
  auto colWidth = (columns.size()) * 3;
  auto baseIndex = compInfo.children(columns[0])[0];
  const auto &baseShapeInfo =
      compInfo.shape(baseIndex).getGeometryHandler()->shapeInfo();
  auto basePos = baseShapeInfo.points()[0];
  std::vector<Mantid::Kernel::V3D> hex(4);

  setBankNormal(baseShapeInfo.points()[1], baseShapeInfo.points()[3], basePos);

  for (size_t x = 0; x < colWidth; x += 3) {
    auto index = x / 3;
    const auto &column = compInfo.children(columns[index]);
    for (size_t y = 0; y < column.size() - 1; ++y) {
      extractHexahedron(compInfo.shape(column[y]), hex);
      offsetHexahedronPosition(hex, -basePos);
      rotateHexahedron(hex, compInfo.rotation(column[y]));
      offsetHexahedronPosition(hex, compInfo.position(column[y]));

      glColor3ub((GLubyte)color[column[y]].red(),
                 (GLubyte)color[column[y]].green(),
                 (GLubyte)color[column[y]].blue());
      glVertex3f(static_cast<GLfloat>(hex[0].X()),
                 static_cast<GLfloat>(hex[0].Y()), 0);
      glVertex3f(static_cast<GLfloat>(hex[1].X()),
                 static_cast<GLfloat>(hex[1].Y()), 0);
      glVertex3f(static_cast<GLfloat>(hex[2].X()),
                 static_cast<GLfloat>(hex[2].Y()), 0);
      glVertex3f(static_cast<GLfloat>(hex[3].X()),
                 static_cast<GLfloat>(hex[3].Y()), 0);
    }
  }

  glEnd();

  if (glGetError() > 0)
    g_log.error() << "OpenGL error in renderStructuredBank() \n";
}
} // namespace BankRenderingHelpers
} // namespace MantidWidgets
} // namespace MantidQt