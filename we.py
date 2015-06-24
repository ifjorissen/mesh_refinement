#
# HOMEWORK 5: See the very bottom 'refine' method in this file,
#             and the description in object-view.py.
#

#
# we.py
#
# Defines object class called "object" that contains a method for
# reading an Alias/Wavefront .obj file and storing its geometry into a
# winged twinned half-edge data structure.  An object ultimately is
# made up of an interlinked collection of three types of data:
#
#   vertex: a corner of a faceted surface.  It has a 3D position 
#           and a set of directed half-edges emanating from it.
#           They serve as the "umbrella spine" of a fan of faces
#           that meet at these corner vertex.
#
#   edge: a directed half-edge that serves as the boundary of 
#         some oriented face of a surface. It may have an 
#         opposite-oriented twin half-edge should they each
#         serve as a crease between two faces.
#
#   face: a triangular face on a surface of the object.  It has 
#         three border half-edges.  

from constants import *
from geometry import vector, point, ORIGIN
from math import sqrt,cos,pi
import sys

#
# class fan
# 
# This is an iterator object that can be used to
# loop through all the edges that emanate from a
# vertex.
# 
class fan:

	#
	# The fan instance attributes:
	#
	# * vertex: the vertex that serves as the center of this fan
	# * which: the current edge being examined during the loop's iteration
	#

	# __init__
	#
	# Creates a fan object for the given vertex,
	#
	def __init__(self,vertex):
			self.vertex = vertex
			self.which = None

	# __iter__
	#
	# (Re)sets this as an iterator for the start of a loop.
	#
	def __iter__(self):
			self.which = self.vertex.edge     # First edge on the fan.
			return self

	# __next__
	#
	# Advances the iterator to the next edge on the fan.
	#
	def __next__(self):

			if self.which == None:
					# If we've exhausted the edges that form the fan, stop.
					raise StopIteration
			else:
					# Otherwise, note where we are in the fan...
					current = self.which

					# ...and advance to the next edge.


					# To advance, make sure that we're not the whole way around...
					if current.next.next.twin != None and \
						 current.next.next.twin != self.vertex.edge:   

							# ...and, if not, advance to the next fan edge.
							self.which = current.next.next.twin

					# Otherwise, signal that we've exhausted our edges.  This
					# "None" signal will be noticed by a subsequent call to 
					# __next__.
					else:
							self.which = None

					# Regardless, give back the current edge.
					return current

#
#  class vertex: 
#
#  Its instances are corners of a faceted surface. 
#  The class also houses a list of all its instances.
#
class vertex:

	# vertex(P,o):
	#
	# (Creates and) initializes a new vertex at position P as part of
	# object o.
	#
	def __init__(self,P,o):
			self.position = P
			self.edge = None
			self.id = len(o.vertex)
			o.vertex.append(self)
			self.vn = None

	#
	# self.set_normal(vn):
	#
	# Sets or changes the normal attached to this vertex.
	#
	def set_normal(self, vn):
			self.vn = vn

	#
	# self.normal():
	#
	# Returns the surface normal at this vertex.  Computes 
	# a normal from the fan of faces around the vertex, were
	# no normal computed yet.
	#
	def normal(self):
			# If there's no normal, compute one.
			if not self.vn:
					# Sum the incident face normals.
					ns = vector(0.0,0.0,0.0)
					for e in self.around():
							ns = ns + e.face.normal()
					# Normalize that sum.
					self.set_normal(ns.unit())

			# Return the normal attribute.
			return self.vn

	#
	# self.color()
	#
	# Returns the material color of this vertex.  For now,
	# we'll just hardwire the color to a medium slate blue.
	def color(self):
			return vector(0.5,0.45,0.57)

	# self.around()
	#
	# This produces an iterator for looping over all the edges
	# that form the fan around a vertex.
	#
	#   for e in V.around():
	#      ... do something with e ...
	#
	# See class "fan" for details, and method "normal" for a 
	# concrete example of its use.
	#
	def around(self):
			return fan(self)

	# self.set_first_edge()
	#
	# Works clockwise around the edge fan of a vertex, setting 
	# its out edge to be the start of that fan.  This is only
	# necessary for "open-fanned" vertices, not those vertices 
	# that are at the tip of a closed fan cone.
	#
	def set_first_edge(self):
			e = self.edge
			while e != None \
						and e.twin != None \
						and e != self.edge:
			
					# If not, then we work backwards to the prior edge.
					e = e.twin.next

			# Otherwise, let's have this be the first out edge.
			self.edge = e

#
# class edge: 
#
# An edge connects two vertices.  It is oriented, and it has a twin
# connected the same two vertices, but in the opposite direction. 
# Each edge has a face to its left, one of the three edges forming
# the counterclockwise border around that face.
#
# The two directed edge twins serve as the meeting crease between 
# two faces.
#
class edge:

	#
	# edge(V1,V2,f):
	#
	# Create an edge from V1 to V2 bordering face f.
	#
	# vertex instance attributes:
	#
	#  * source: first vertex of the vertex pair
	#  * face: left face bordered by this edge
	#  * next: next edge bordering the same face
	#  * twin: the twin edge to this edge
	#  * o: the object that has this edge
	#
	def __init__(self,V1,V2,f,o):

			self.source = V1  # Set the source vertex.
			V1.edge = self    # Register edge with the source vertex.
			self.face = f     # Set the face.

			self.next = None  # Will be set later.

			# Register this edge.
			iv1 = V1.id
			iv2 = V2.id
			if (iv1,iv2) in o.edge:
					print('Bad orientation for face ',f, iv1, iv2)
			o.edge[(iv1,iv2)] = self

			# Check if this edge has a twin yet.
			self.twin = None
			if (iv2,iv1) in o.edge:
					# Update the twin info of its twin.
					self.twin = o.edge[(iv2,iv1)]
					self.twin.twin = self
	
	# 
	# self.vertex(i):
	#
	# Get either the source (i=0) or the target vertex (i=1) of
	# this directed edge.
	#
	def vertex(self,i):
			if i == 0:
					return self.source
			elif i == 1:
					return self.next.source
			else:
					return None

	# 
	# self.vector():
	#
	# Returns the offset between the two vertices.
	#
	def vector(self):
			return self.vertex(1).position - self.vertex(0).position

	# 
	# self.direction():
	#
	# Returns the direction of the offset between the 
	# two vertices.
	#
	def direction(self):
			return self.vector().unit()


	def __str__(self):
			return '<edge '+str(self.vertex(0).id)+':'+str(self.vertex(1).id)+'>'
#
# class face: 
#
# Its instances are triangular facets on the surface.  It has three
# vertices as its corners and three edges that serve as its boundary.
#
class face:

	#
	# face(V1,V2,V3,o):
	#
	# Create and initialize a new face instance.
	#
	# Instance attributes:
	#
	#   * side: one of the three directed edges
	#   * fn: face normal
	#   * id: integer id identifying this vertex
	#   * o: object that this is part of
	#
	def __init__(self,V1,V2,V3,o):

			e1 = edge(V1,V2,self,o)
			e2 = edge(V2,V3,self,o)
			e3 = edge(V3,V1,self,o)

			e1.next = e2
			e2.next = e3
			e3.next = e1
			
			self.side = e1
			self.id = len(o.face)
			o.face.append(self)
			self.fn = None

	#
	# self.normal():
	#
	# Returns the surface normal at this vertex.  Computes 
	# a normal if it hasn't been computed yet.
	#
	def normal(self):
			if not self.fn:
					e0 = self.edge(0).direction()
					e1 = self.edge(1).direction()
					self.fn = e0.cross(e1)

			return self.fn

	#
	# self.vertex(i):
	# 
	# Returns either the 0th, the 1st, or the 2nd vertex.
	#
	def vertex(self,i):
			if i > 2:
					return None
			else:
					return self.edge(i).source

	#
	# self.edges():
	# 
	# Returns list of the three edges around this face.
	#
	def edges(self):
			return [self.side,self.side.next,self.side.next.next]
	#
	# self.edge(i):
	# 
	# Returns either the 0th, the 1st, or the 2nd boundary edge.
	#
	def edge(self,i):
			if i == 0:
					return self.side
			elif i == 1:
					return self.side.next
			elif i == 2:
					return self.side.next.next
			else:
					return None

#
# class object:
#
# Winged-edge representation of an .obj file, or its finer meshes.
#
class object:

	def __init__(self):
			self.vertex = []
			self.edge = {}
			self.face = []

	#
	# o.read(f)
	#
	# Reads the contents of an .OBJ file into instance 'o' as
	# vertices, (normals), and faces.  Build the W-E'd representation
	# of the object described.
	#
	# The end result is a linked data structure, referencable
	# by a vertex list 'o.vertex', an edge index pair dictionary
	# 'o.edge', and a face list 'o.face'.  
	#
	def read(self,filename):

		obj_file = open(filename,'r')
		normali = 0

		for line in obj_file:

			# Parse a line.
			parts = line[:-1].split()
			if len(parts) > 0:

				# Read a vertex description line.
				if parts[0] == 'v': 
					x = float(parts[1])
					y = float(parts[2])
					z = float(parts[3])
					P = point(x,y,z)
					vertex(P,self)

				# Read a vertex normal description line.
				elif parts[0] == 'vn': 
					dx = float(parts[1])
					dy = float(parts[2])
					dz = float(parts[3])
					vn = vector(dx,dy,dz).unit()
					self.vertex[normali].set_normal(vn)
					normali += 1

				# Read a face/fan description line.
				elif parts[0] == 'f': 

					vi_fan = [int(p.split('/')[0]) - 1 for p in parts[1:]]

					vi1 = vi_fan[0]
					# add the faces of the fan
					for i in range(1,len(vi_fan)-1):
						vi2 = vi_fan[i]
						vi3 = vi_fan[i+1]

						V1 = self.vertex[vi1]
						V2 = self.vertex[vi2]
						V3 = self.vertex[vi3]

						face(V1,V2,V3,self)

		# Wrap up the vertex fans.  Re-chooses each vertex's out edge.
		self.finish()

		# Rescale and center the points.
		self.rebox()


	# o.finish()
	#
	# This needs to be called after the W-E'd structure for an 
	# object is built.  For each vertex 'V' in 'o', this goes 
	# through the edges that have 'V' as a source and, if that
	# vertex is at the tip of a fan rather than a cone, it
	# finds the out edge that is first on that fan (in CCW ordering).
	#
	def finish(self):
		# set the vertex fan ordering
		for V in self.vertex:
				V.set_first_edge()

	# o.rebox()
	#
	# This normalizes the vertex positions so that the fit within a
	# canonical volume.  I could have used OpenGL's transformations to
	# do this but I found that, by changing the geometry instead, my
	# code was much easier to debug.
	#
	def rebox(self):
		max_dims = point(sys.float_info.min,
										 sys.float_info.min,
										 sys.float_info.min)
		min_dims = point(sys.float_info.max,
										 sys.float_info.max,
										 sys.float_info.max)
		for V in self.vertex:
				max_dims = max_dims.max(V.position)
				min_dims = min_dims.min(V.position)

		span = max_dims - min_dims
		center = point((min_dims.x + max_dims.x)/2.0,
									 min_dims.y,
									 (min_dims.z + max_dims.z)/2.0)
		scale = 1.4/abs(max_dims - center)

		for V in self.vertex:
				V.position = ORIGIN + scale * (V.position-center)

	# o.compile()
	#
	# Produces a triple of lists that are used to build the 
	# VBOs for rendering this object in hardware.
	#
	# Returns a packed array of floats corresponding to
	# the vertex positions, vertex normal directions, and
	# the vertex colors.
	#
	def compile(self):
		varray = []
		narray = []
		carray = []
		for f in self.face:
			for i in [0,1,2]:
				varray.extend(f.vertex(i).position.components())
				narray.extend(f.vertex(i).normal().components())
				carray.extend(f.vertex(i).color().components())
		return (varray,narray,carray)

	#
	# o' = o.refine()
	# refines an object using Loop's subdivision
	#
	def refine(self):
		selfie = object()
		vclones = {} 
		vnew = {}

		#create four faces: splitting phase
		for f in self.face:
			nvpts = []
			for edge in f.edges():
				if edge.source not in vclones:
					vclones[edge.source] = vertex(edge.source.position, selfie)

				#make the new vertex
				nvec = edge.vector().scale(1/2)
				nvpos = edge.source.position.plus(nvec)
				nv = vertex(nvpos, selfie)

				if edge.twin is not None and edge.twin in vnew:
					nvp = vnew[edge.twin]
					nvpts.append(nvp)
					selfie.vertex.pop()

				#add the vertex introduced at this edge
				#the edge is the key, the new vertex is the value
				elif edge.twin not in vnew:
					vnew[edge] = nv
					nvpts.append(vnew[edge])
				else:
					print("error")

			#create the faces
			for i in range(0,3):
				face(vclones[f.edge(i).source], nvpts[i], nvpts[(i+2)%3], selfie)
			face(nvpts[0], nvpts[1], nvpts[2], selfie)

		selfie.finish()

		#Debugging
		# print ("number of faces in self.face: " + str(len(self.face)))
		# print ("number of faces in selfie.face: " + str(len(selfie.face)))
		# print ("number of edges in self.edge: " + str(len(self.edge)))
		# print ("number of edges in selfie.edge: " + str(len(selfie.edge)))
		# print ("number of vertices in self.vertex: " + str(len(self.vertex)))
		# print ("number of vertices in selfie.vertex: " + str(len(selfie.vertex)))

		# averaging phase
		# recompute the position of all of the vertices that were part of the original shape
		for v in vclones:
			sv = vclones[v]
			ps = [e.vertex(1).position for e in sv.around()]
			count = len(ps)
			ss = [1.0/count] * count
			centroid = v.position.combos(ss,ps)

			#we're on a cone 
			if sv.edge.twin is not None:
				bn = 5.0/8.0 - (3.0/8.0 + 2.0*cos((2.0*pi)/count)/8.0) ** 2
				yn = bn / (1.0 - bn)
				an = (yn/(1.0+yn))
				dn = (1.0/(1.0+yn))
				# sve = sv.position.components()
				fvec = [x*an + y*dn for x,y in zip(sv.position.components(), centroid)]
				sv.position = point(fvec[0], fvec[1], fvec[2])

			#otherwise, we're on a fan
			else:
				vn1 = cur.source.position.minus(ORIGIN).scale(1/8)
				v0 = sv.edge.vertex(1).position.minus(ORIGIN).scale(1/8)
				vp = sv.edge.vector().scale(3/4)
				nvec = vp.plus(v0).plus(vn1)
				sv.position = point(nvec[0], nvec[1], nvec[2])

		#recompute the position of the vertices that are new
		for v in vnew.values():
			e0 = v.edge
			#case 1: interior edge on boundary
			if e0.twin is None:
				fvec = [(1/2)*(x + y) for x,y in zip(v.position.components(), e0.vertex(1).position.components())]
				v.position = point(fvec[0], fvec[1], fvec[2])

			#case 2: split interior edge
			else:
				e1 = e0.twin
				v1 = e1.source
				f0 = e0.next.next.source
				f1 = e1.next.next.source
				fs = [(1/8) * (x+y) for x, y in zip(f1.position.components(), f0.position.components())]
				vs = [(3/8) * (x+y) for x, y in zip(v.position.components(), v1.position.components())]
				fvec = [x + y for x, y in zip(fs, vs)]
				v.position = point(fvec[0], fvec[1], fvec[2])

		return selfie





















