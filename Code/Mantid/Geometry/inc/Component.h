#ifndef COMPONENT_H_
#define COMPONENT_H_
#include <string>
#include "V3D.h"
#include "Quat.h"
#include "MantidKernel/System.h"

namespace Mantid
{
namespace Geometry
{
	
	// Forward declarations 
	// end forward declarations
/** @class Component
      @brief base class for Geometric component
      @version A
      @author Laurent C Chapon, ISIS RAL
      @date 01/11/2007
      
      This is the base class for geometric components.
      Geometric component can be placed in a hierarchical
      structure and are defined with respect to a
      parent component. The component position and orientation
      are relatives, i.e. defined with respect to the parent 
      component. The orientation is stored as a quaternion.
      Each component has a defined bounding box which at the moment 
      is cuboid.

      Copyright 2007 RAL

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
	    
      File change history is stored at: 
      <https://svn.mantidproject.org/mantid/trunk/Code/Mantid>
  */
class DLLExport Component
{
public:
	virtual std::string type() const {return "LogicalComponent";}
	//! Create Empty Component at Origin, with no orientation and null parent
	Component();
	//! Create a named component with a parent component (optional)
	Component(const std::string&, Component* reference=0);
	//! Create a named component with positioning vector, and parent component (optional)
	Component(const std::string&, const V3D&, Component* reference=0);
	//! Create a named component with positioning vector, orientation and parent component
	Component(const std::string&, const V3D&, const Quat&, Component* reference=0);
	//Copy constructors
	//! Copy constructor
	Component(const Component&);
	//Component& operator=(const Component&);
	//! Return a clone to the current object
	virtual Component* clone() const;
	virtual ~Component();
	//! Assign a parent component. Previous parent link is lost
	void setParent(Component*);
	//! Return a pointer to the current parent.
	const Component* getParent() const;
	//! Set the component name
	void setName(const std::string&);
	//! Get the component name
	std::string getName() const;
	//! Set the component position, x, y, z respective to parent (if present) otherwise absolute
	void setPos(double, double, double);
	void setPos(const V3D&);
	//! Set the orientation quaternion relative to parent (if present) otherwise absolute
	void setRot(const Quat&);
	//! Copy the Rotation from another component
	void copyRot(const Component&);
	//! Translate the component (vector form). This is relative to parent if present.
	void translate(const V3D&);
	//! Translate the component (x,y,z form). This is relative to parent if present.
	void translate(double, double, double);
	//! Rotate the component. This is relative to parent. 
	void rotate(const Quat&);
	//! Rotate the component by an angle in degrees with respect to an axis.
	void rotate(double,const V3D&);
	//! Get the position relative to the parent component (absolute if no parent)
	V3D getRelativePos() const;
	//! Get the position of the component. Tree structure is traverse through the parent chain
	V3D getPos() const;
	//! Get the relative Orientation
	const Quat& getRelativeRot() const;
	//! Get the distance to another component
	double getDistance(const Component&) const;
	void printSelf(std::ostream&) const;
private:
  //! Name of the component
	std::string name;
	//! Position w
	V3D pos;
	//! Orientation 
	Quat rot;
	Component* parent;   // Parent component in the tree
};

std::ostream& operator<<(std::ostream&, const Component&);

} //Namespace Geometry
} //Namespace Mantid

#endif /*COMPONENT_H_*/
