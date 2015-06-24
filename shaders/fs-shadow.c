#version 120

uniform int wires;
varying vec3 bcoord;

void main() {

  vec3 diff = fwidth(bcoord);

  bool edge = (bcoord[0] < diff[0]*0.5 
	       || bcoord[1] < diff[1]*0.5 
	       || bcoord[2] < diff[2]*0.5);

  if (wires==1 && edge) {
    gl_FragColor = vec4(0.5,0.5,0.55,1.0);
  } else {
    vec3 ambient_c = 0.25 * vec3(0.5, 0.6, 0.55);   
    gl_FragColor = vec4(ambient_c,1.0);
  }
}
