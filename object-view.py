#
# object-view.py
#
# Author: Jim Fix
# MATH 385, Reed College, Spring 2015
#
# This is the starting point for Homework 5 where you
# are asked to implememt C. Loop's subdivision scheme.
# It relies on the separate file 'we.py' which implements
# object, face, edge, and vertex classes.  These 
# constitute a triangular mesh that describe an object.
#
# In the code below, that object/mesh is constructed from
# an Alias/Wavefront .OBJ file and displayed in an OpenGL
# window.  It can then be 'refined' by pressing the '/'
# key.  The effect should be to build a new mesh, one 
# where each triangular face of the 'input mesh' is 
# split into four triangles, and where the placement of
# their vertices is a weighted average of vertices on
# and around the split face.  The resulting 'output
# mesh' object replaces pre-refined input mesh, and 
# becomes what's displayed by the code below.
#
# The refinement happens in the 'slash key handler'
# code under the procedure 'keypress'.
#
# Your assignment is to modify the 'refine' method code 
# at the bottom of 'we.py', under the definition of 
# the 'object' class, so that it performs Loop's
# splitting and averaging and returns that new, refined
# mesh.
#
# To run the code:
#    python3 object-view.py objs/stell.obj
#
# There are several interesting low-resolution meshes found
# in the 'objs' folder.
#

import sys
from geometry import point, vector, EPSILON, ORIGIN
from quat import quat
from we import vertex, edge, face, object
from random import random
from math import sin, cos, acos, asin, pi, sqrt
from ctypes import *

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLUT.freeglut import *

trackball = None   # Orientation of the mesh.
flashlight = None  # Light position illuminating the object.

vertex_buffer = None  # The VBOs
normal_buffer = None  #
color_buffer = None   #

shaders = None    # The two shading programs.
shadowers = None  #

wireframe = 0  # Show the wireframe?  1 means 'Yes.'
mesh = None    # The mesh of facets of the object
mesh0 = None   # Perhaps keep around the control mesh.

xStart = 0
yStart = 0
width = 512
height = 512
scale = 1.0/min(width,height)

def init_shaders(vs_name,fs_name):
    """Compile the vertex and fragment shaders from source."""

    vertex_shader = glCreateShader(GL_VERTEX_SHADER)
    glShaderSource(vertex_shader,open(vs_name,'r').read())
    glCompileShader(vertex_shader)
    result = glGetShaderiv(vertex_shader, GL_COMPILE_STATUS)
    if result:
        print('Vertex shader compilation successful.')
    else:
        print('Vertex shader compilation FAILED:')
        print(glGetShaderInfoLog(vertex_shader))
        sys.exit(-1)

    fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
    glShaderSource(fragment_shader, open(fs_name,'r').read())
    glCompileShader(fragment_shader)
    result = glGetShaderiv(fragment_shader, GL_COMPILE_STATUS)
    if result:
        print('Fragment shader compilation successful.')
    else:
        print('Fragment shader compilation FAILED:')
        print(glGetShaderInfoLog(fragment_shader))
        sys.exit(-1)

    shs = glCreateProgram()
    glAttachShader(shs,vertex_shader)
    glAttachShader(shs,fragment_shader)
    glLinkProgram(shs)

    return shs


def draw():
    """ Issue GL calls to draw the scene. """
    global trackball, flashlight, \
           vertex_buffer, normal_buffer, color_buffer, \
           shaders, wireframe, mesh

    # Clear the rendering information.
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # Clear the transformation stack.
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glPushMatrix()

    # Transform the objects drawn below by a rotation.
    trackball.glRotate()

    # * * * * * * * * * * * * * * * *
    # Draw all the triangular facets.
    shs = shaders
    glUseProgram(shs)
    h_vertex = glGetAttribLocation(shs,'vertex')
    h_normal = glGetAttribLocation(shs,'normal')
    h_color =  glGetAttribLocation(shs,'color')
    h_bary =   glGetAttribLocation(shs,'bary')
    h_eye =    glGetUniformLocation(shs,'eye')
    h_light =  glGetUniformLocation(shs,'light')
    h_wires =  glGetUniformLocation(shs,'wires')

    # all the vertex positions
    glEnableVertexAttribArray(h_vertex)
    glBindBuffer (GL_ARRAY_BUFFER, vertex_buffer)
    glVertexAttribPointer(h_vertex, 3, GL_FLOAT, GL_FALSE, 0, None)
        
    # all the vertex normals
    glEnableVertexAttribArray(h_normal)
    glBindBuffer (GL_ARRAY_BUFFER, normal_buffer)
    glVertexAttribPointer(h_normal, 3, GL_FLOAT, GL_FALSE, 0, None)

    # all the face vertex colors
    glEnableVertexAttribArray(h_color)
    glBindBuffer (GL_ARRAY_BUFFER, color_buffer)
    glVertexAttribPointer(h_color, 3, GL_FLOAT, GL_FALSE, 0, None)

    # all the vertex barycentric labels
    glEnableVertexAttribArray(h_bary)
    glBindBuffer (GL_ARRAY_BUFFER, bary_buffer)
    glVertexAttribPointer(h_bary, 3, GL_FLOAT, GL_FALSE, 0, None)
        
    # position of the flashlight
    light = flashlight.rotate(vector(0.0,1.0,0.0));
    glUniform3fv(h_light, 1, (4.0*light).components())

    # position of the viewer's eye
    eye = trackball.recip().rotate(vector(0.0,0.0,1.0))
    glUniform3fv(h_eye, 1, eye.components())

    # show wireframe?
    glUniform1i(h_wires, wireframe)

    glDrawArrays (GL_TRIANGLES, 0, len(mesh.face) * 3)

    glDisableVertexAttribArray(h_vertex)
    glDisableVertexAttribArray(h_normal)
    glDisableVertexAttribArray(h_color)
    glDisableVertexAttribArray(h_bary)


    # * * * * * * * * * * * * * * * *
    # Draw the object's shadow
    shs = shadowers
    glUseProgram(shs)
    h_vertex = glGetAttribLocation(shs,'vertex')
    h_bary = glGetAttribLocation(shs,'bary')
    h_normal = glGetUniformLocation(shs,'normal')
    h_plane = glGetUniformLocation(shs,'plane')
    h_light =  glGetUniformLocation(shs,'light')
    h_wires =  glGetUniformLocation(shs,'wires')

    # all the vertex positions
    glEnableVertexAttribArray(h_vertex)
    glBindBuffer (GL_ARRAY_BUFFER, vertex_buffer)
    glVertexAttribPointer(h_vertex, 3, GL_FLOAT, GL_FALSE, 0, None)

    # all the vertex barycentric labels
    glEnableVertexAttribArray(h_bary)
    glBindBuffer (GL_ARRAY_BUFFER, bary_buffer)
    glVertexAttribPointer(h_bary, 3, GL_FLOAT, GL_FALSE, 0, None)
        
    # position of the flashlight
    light = flashlight.rotate(vector(0.0,1.0,0.0));
    glUniform3fv(h_light, 1, (4.0*light).components())

    # position of the plane
    glUniform3fv(h_plane, 1, [0.0,-0.50,0.0])

    # normal to the plane's surface
    glUniform3fv(h_normal, 1, [0.0,+1.0,0.0])

    # Show as a wireframe? No.
    # glUniform1i(h_wires, wireframe)
    glUniform1i(h_wires, 0)

    glDrawArrays (GL_TRIANGLES, 0, len(mesh.face) * 3)

    glDisableVertexAttribArray(h_vertex)
    glDisableVertexAttribArray(h_bary)

    glPopMatrix()

    # Render the scene.
    glFlush()

    glutSwapBuffers()


def keypress(key, x, y):
    """ Handle a "normal" keypress. """
    global wireframe, mesh, control

    # Handle ESC key.
    if key == b'\033':	
	# "\033" is the Escape key
        sys.exit(1)

    # Handle SPACE key.
    if key == b' ':	
        wireframe = 1 - wireframe
        glutPostRedisplay()

    # Handle slash key.
    if key == b'/':	
        mesh = mesh.refine()
        vbo_ify(mesh)
        glutPostRedisplay()

    # Handle slash key.
    if key == b'm':	
        control = not control
        glutPostRedisplay()


def arrow(key, x, y):
    """ Handle a "special" keypress. """
    global trackball,flashlight

    if key == GLUT_KEY_DOWN or key == GLUT_KEY_UP:
        axis = trackball.recip().rotate(vector(1.0,0.0,0.0))
    if key == GLUT_KEY_LEFT or key == GLUT_KEY_RIGHT:
        axis = trackball.recip().rotate(vector(0.0,1.0,0.0))
    if key == GLUT_KEY_LEFT or key == GLUT_KEY_DOWN:
        angle = -pi/12.0
    if key == GLUT_KEY_RIGHT or key == GLUT_KEY_UP:
        angle = pi/12.0

    if key in {GLUT_KEY_LEFT,GLUT_KEY_RIGHT,GLUT_KEY_UP,GLUT_KEY_DOWN}:
        # Apply an adjustment to the position of the light.
        flashlight = quat.for_rotation(angle,axis) * flashlight
        # Redraw.
        glutPostRedisplay()

def world(mousex,mousey):
    x = 2.0 * (mousex - width/2) / min(width,height)
    y = 2.0 * (height/2 - mousey) / min(width,height)
    return (x,y)

def mouse(button, state, x, y):
    global xStart, yStart
    xStart, yStart = world(x,y)
    glutPostRedisplay()

def motion(x, y):
    global trackball, xStart, yStart
    xNow, yNow = world(x,y)
    dx = xNow-xStart
    dy = yNow-yStart
    axis = vector(-dy,dx,0.0).unit()
    angle = asin(min(sqrt(dx*dx+dy*dy),1.0))
    trackball = quat.for_rotation(angle,axis) * trackball
    xStart = xNow
    yStart = yNow
    glutPostRedisplay()

def vbo_ify(mesh):
    global vertex_buffer, normal_buffer, color_buffer, bary_buffer

    vertices, normals, colors = mesh.compile()

    nf = len(mesh.face)

    barys = [1.0,0.0,0.0, 0.0,1.0,0.0, 0.0,0.0,1.0]*nf
    
    vertex_buffer = glGenBuffers(1)
    glBindBuffer (GL_ARRAY_BUFFER, vertex_buffer)
    glBufferData (GL_ARRAY_BUFFER, len(vertices)*4, 
                  (c_float*len(vertices))(*vertices), GL_STATIC_DRAW)

    normal_buffer = glGenBuffers(1)
    glBindBuffer (GL_ARRAY_BUFFER, normal_buffer)
    glBufferData (GL_ARRAY_BUFFER, len(normals)*4, 
                  (c_float*len(normals))(*normals), GL_STATIC_DRAW)

    color_buffer = glGenBuffers(1)
    glBindBuffer (GL_ARRAY_BUFFER, color_buffer)
    glBufferData (GL_ARRAY_BUFFER, len(colors)*4, 
                  (c_float*len(colors))(*colors), GL_STATIC_DRAW)

    bary_buffer = glGenBuffers(1)
    glBindBuffer (GL_ARRAY_BUFFER, bary_buffer)
    glBufferData (GL_ARRAY_BUFFER, len(barys)*4, 
                  (c_float*len(barys))(*barys), GL_STATIC_DRAW)

def init(filename):
    """ Initialize aspects of the GL scene rendering.  """
    global trackball, flashlight, \
           shaders, shadowers, mesh, mesh0

    # Initialize quaternions for the light and trackball
    flashlight = quat.for_rotation(0.0,vector(1.0,0.0,0.0))
    trackball = quat.for_rotation(0.0,vector(1.0,0.0,0.0))

    # Read the .OBJ file into VBOs.
    mesh0 = object()
    mesh0.read(filename)
    vbo_ify(mesh0)
    mesh = mesh0

    # Set up the shaders.
    shaders = init_shaders('shaders/vs-mesh.c',
                           'shaders/fs-mesh.c')
    shadowers = init_shaders('shaders/vs-shadow.c',
                             'shaders/fs-shadow.c')
                 
    # Set up OpenGL state.
    glEnable (GL_DEPTH_TEST)


def resize(w, h):
    """ Register a window resize by changing the viewport.  """
    global width, height, scale

    glViewport(0, 0, w, h)
    width = w
    height = h

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    if w > h:
        glOrtho(-w/h, w/h, -1.0, 1.0, -10.0, 10.0)
        scale = 2.0 / h 
    else:
        glOrtho(-1.0, 1.0, -h/w, h/w, -10.0, 10.0)
        scale = 2.0 / w 


def run(filename):
    """ The main procedure, sets up GL and GLUT. """

    # Initialize the GLUT window.
    glutInit([])
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowPosition(0, 20)
    glutInitWindowSize(width, height)
    glutCreateWindow( 'object-view.py - Press ESC to quit' )

    # Initialize the object viewer's state.
    init(filename)

    # Register interaction callbacks.
    glutKeyboardFunc(keypress)
    glutSpecialFunc(arrow)
    glutReshapeFunc(resize)
    glutDisplayFunc(draw)
    glutMouseFunc(mouse)
    glutMotionFunc(motion)

    # Issue some instructions.
    print()
    print('Drag the object with the mouse to reorient it.')
    print('Press the arrow keys move the flashlight.')
    print('Press SPACE to show the mesh.')
    print('Press "/" to refine the mesh.')
    print('Press ESC to quit.')
    print()

    glutMainLoop()
    return 0


if len(sys.argv) > 1:
    run(sys.argv[1])
else:
    run('objs/stell.obj')
