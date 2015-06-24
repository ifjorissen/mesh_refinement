#version 120

attribute vec3 vertex;   // location on the surface
attribute vec3 normal;   // normal direction of the surface at location
attribute vec3 color;    // material properties of the surface at location
attribute vec3 bary;    // material properties of the surface at location

uniform vec3 light;      // position of a point light source
uniform vec3 eye;        // position of the eyepoint
uniform int wires;

varying vec3 n;
varying vec3 P;
varying vec3 material_c;
varying vec3 bcoord;

void main() {
  n = normal;
  P = vertex;
  material_c = color;
  bcoord = bary;
  gl_Position = gl_ProjectionMatrix*gl_ModelViewMatrix*vec4(P,1.0);
}
