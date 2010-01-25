"Code snippets for code generation."

__author__ = "Anders Logg (logg@simula.no)"
__date__ = "2007-02-28"
__copyright__ = "Copyright (C) 2007 Anders Logg"
__license__  = "GNU GPL version 3 or any later version"

# Modified by Kristian B. Oelgaard 2010
# Modified by Marie Rognes 2007 -- 2010
# Modified by Peter Brune 2009
# Last changed: 2010-01-25

# Code snippets

__all__ = ["header_ufc", "header_dolfin", "footer",
           "cell_coordinates", "jacobian", "inverse_jacobian",
           "evaluate_f",
           "facet_determinant", "map_onto_physical",
           "fiat_coordinate_map", "transform_snippet",
           "scale_factor", "combinations_snippet",
           "normal_direction",
           "facet_normal"]

header_ufc = """\
// This code conforms with the UFC specification version %(ufc_version)s
// and was automatically generated by FFC version %(ffc_version)s.

#ifndef __%(prefix_upper)s_H
#define __%(prefix_upper)s_H

#include <cmath>
#include <stdexcept>
#include <ufc.h>"""

header_dolfin = """\
// This code conforms with the UFC specification version %(ufc_version)s
// and was automatically generated by FFC version %(ffc_version)s.
//
// This code was generated with the option '-l dolfin' and
// contains DOLFIN-specific wrappers that depend on DOLFIN.

#ifndef __%(prefix_upper)s_H
#define __%(prefix_upper)s_H

#include <cmath>
#include <stdexcept>
#include <fstream>
#include <ufc.h>"""

footer = """\
#endif"""

cell_coordinates = "const double * const * x = c.coordinates;\n"

# Code snippets for computing Jacobian
_jacobian_1D = """\
// Extract vertex coordinates
const double * const * x%(restriction)s = c%(restriction)s.coordinates;

// Compute Jacobian of affine map from reference cell
const double J%(restriction)s_00 = x%(restriction)s[1][0] - x%(restriction)s[0][0];"""

_jacobian_2D = """\
// Extract vertex coordinates
const double * const * x%(restriction)s = c%(restriction)s.coordinates;

// Compute Jacobian of affine map from reference cell
const double J%(restriction)s_00 = x%(restriction)s[1][0] - x%(restriction)s[0][0];
const double J%(restriction)s_01 = x%(restriction)s[2][0] - x%(restriction)s[0][0];
const double J%(restriction)s_10 = x%(restriction)s[1][1] - x%(restriction)s[0][1];
const double J%(restriction)s_11 = x%(restriction)s[2][1] - x%(restriction)s[0][1];"""

_jacobian_3D = """\
// Extract vertex coordinates
const double * const * x%(restriction)s = c%(restriction)s.coordinates;

// Compute Jacobian of affine map from reference cell
const double J%(restriction)s_00 = x%(restriction)s[1][0] - x%(restriction)s[0][0];
const double J%(restriction)s_01 = x%(restriction)s[2][0] - x%(restriction)s[0][0];
const double J%(restriction)s_02 = x%(restriction)s[3][0] - x%(restriction)s[0][0];
const double J%(restriction)s_10 = x%(restriction)s[1][1] - x%(restriction)s[0][1];
const double J%(restriction)s_11 = x%(restriction)s[2][1] - x%(restriction)s[0][1];
const double J%(restriction)s_12 = x%(restriction)s[3][1] - x%(restriction)s[0][1];
const double J%(restriction)s_20 = x%(restriction)s[1][2] - x%(restriction)s[0][2];
const double J%(restriction)s_21 = x%(restriction)s[2][2] - x%(restriction)s[0][2];
const double J%(restriction)s_22 = x%(restriction)s[3][2] - x%(restriction)s[0][2];"""


# Code snippets for computing the inverse Jacobian. Assumes that
# Jacobian is already initialized
_inverse_jacobian_1D = """\

const double K%(restriction)s_00 =  1.0/J%(restriction)s_00;"""

_inverse_jacobian_2D = """\

// Compute determinant of Jacobian
double detJ%(restriction)s = J%(restriction)s_00*J%(restriction)s_11 - J%(restriction)s_01*J%(restriction)s_10;

// Compute inverse of Jacobian
const double K%(restriction)s_00 =  J%(restriction)s_11 / detJ%(restriction)s;
const double K%(restriction)s_01 = -J%(restriction)s_01 / detJ%(restriction)s;
const double K%(restriction)s_10 = -J%(restriction)s_10 / detJ%(restriction)s;
const double K%(restriction)s_11 =  J%(restriction)s_00 / detJ%(restriction)s;"""

_inverse_jacobian_3D = """\

// Compute sub determinants
const double d00 = J%(restriction)s_11*J%(restriction)s_22 - J%(restriction)s_12*J%(restriction)s_21;
const double d01 = J%(restriction)s_12*J%(restriction)s_20 - J%(restriction)s_10*J%(restriction)s_22;
const double d02 = J%(restriction)s_10*J%(restriction)s_21 - J%(restriction)s_11*J%(restriction)s_20;

const double d10 = J%(restriction)s_02*J%(restriction)s_21 - J%(restriction)s_01*J%(restriction)s_22;
const double d11 = J%(restriction)s_00*J%(restriction)s_22 - J%(restriction)s_02*J%(restriction)s_20;
const double d12 = J%(restriction)s_01*J%(restriction)s_20 - J%(restriction)s_00*J%(restriction)s_21;

const double d20 = J%(restriction)s_01*J%(restriction)s_12 - J%(restriction)s_02*J%(restriction)s_11;
const double d21 = J%(restriction)s_02*J%(restriction)s_10 - J%(restriction)s_00*J%(restriction)s_12;
const double d22 = J%(restriction)s_00*J%(restriction)s_11 - J%(restriction)s_01*J%(restriction)s_10;

// Compute determinant of Jacobian
double detJ%(restriction)s = J%(restriction)s_00*d00 + J%(restriction)s_10*d10 + J%(restriction)s_20*d20;

// Compute inverse of Jacobian
const double K%(restriction)s_00 = d00 / detJ%(restriction)s;
const double K%(restriction)s_01 = d10 / detJ%(restriction)s;
const double K%(restriction)s_02 = d20 / detJ%(restriction)s;
const double K%(restriction)s_10 = d01 / detJ%(restriction)s;
const double K%(restriction)s_11 = d11 / detJ%(restriction)s;
const double K%(restriction)s_12 = d21 / detJ%(restriction)s;
const double K%(restriction)s_20 = d02 / detJ%(restriction)s;
const double K%(restriction)s_21 = d12 / detJ%(restriction)s;
const double K%(restriction)s_22 = d22 / detJ%(restriction)s;"""

evaluate_f = "f.evaluate(vals, y, c);"

scale_factor = """\
// Set scale factor
const double det = std::abs(detJ);"""

_facet_determinant_1D = """\
// Facet determinant 1D (vertex)
const double det = 1.0;"""

_facet_determinant_2D = """\
// Get vertices on edge
static unsigned int edge_vertices[3][2] = {{1, 2}, {0, 2}, {0, 1}};
const unsigned int v0 = edge_vertices[facet%(restriction)s][0];
const unsigned int v1 = edge_vertices[facet%(restriction)s][1];

// Compute scale factor (length of edge scaled by length of reference interval)
const double dx0 = x%(restriction)s[v1][0] - x%(restriction)s[v0][0];
const double dx1 = x%(restriction)s[v1][1] - x%(restriction)s[v0][1];
const double det = std::sqrt(dx0*dx0 + dx1*dx1);"""

_facet_determinant_3D = """\
// Get vertices on face
static unsigned int face_vertices[4][3] = {{1, 2, 3}, {0, 2, 3}, {0, 1, 3}, {0, 1, 2}};
const unsigned int v0 = face_vertices[facet%(restriction)s][0];
const unsigned int v1 = face_vertices[facet%(restriction)s][1];
const unsigned int v2 = face_vertices[facet%(restriction)s][2];

// Compute scale factor (area of face scaled by area of reference triangle)
const double a0 = (x%(restriction)s[v0][1]*x%(restriction)s[v1][2]
                 + x%(restriction)s[v0][2]*x%(restriction)s[v2][1]
                 + x%(restriction)s[v1][1]*x%(restriction)s[v2][2])
                - (x%(restriction)s[v2][1]*x%(restriction)s[v1][2]
                 + x%(restriction)s[v2][2]*x%(restriction)s[v0][1]
                 + x%(restriction)s[v1][1]*x%(restriction)s[v0][2]);

const double a1 = (x%(restriction)s[v0][2]*x%(restriction)s[v1][0]
                 + x%(restriction)s[v0][0]*x%(restriction)s[v2][2]
                 + x%(restriction)s[v1][2]*x%(restriction)s[v2][0])
                - (x%(restriction)s[v2][2]*x%(restriction)s[v1][0]
                 + x%(restriction)s[v2][0]*x%(restriction)s[v0][2]
                + x%(restriction)s[v1][2]*x%(restriction)s[v0][0]);

const double a2 = (x%(restriction)s[v0][0]*x%(restriction)s[v1][1]
                 + x%(restriction)s[v0][1]*x%(restriction)s[v2][0]
                 + x%(restriction)s[v1][0]*x%(restriction)s[v2][1])
                - (x%(restriction)s[v2][0]*x%(restriction)s[v1][1]
                 + x%(restriction)s[v2][1]*x%(restriction)s[v0][0]
                 + x%(restriction)s[v1][0]*x%(restriction)s[v0][1]);

const double det = std::sqrt(a0*a0 + a1*a1 + a2*a2);"""

_normal_direction_1D = ""

_normal_direction_2D = """\
const bool direction = dx1*(x%(restriction)s[%(facet)s][0] - x%(restriction)s[v0][0]) - dx0*(x%(restriction)s[%(facet)s][1] - x%(restriction)s[v0][1]) < 0;"""

_normal_direction_3D = """\
const bool direction = a0*(x%(restriction)s[%(facet)s][0] - x%(restriction)s[v0][0]) + a1*(x%(restriction)s[%(facet)s][1] - x%(restriction)s[v0][1])  + a2*(x%(restriction)s[%(facet)s][2] - x%(restriction)s[v0][2]) < 0;"""

_facet_normal_1D = """\
// Compute facet normals from the facet scale factor constants
// FIXME: not implemented"""

_facet_normal_2D = """\
// Compute facet normals from the facet scale factor constants
const double n%(restriction)s0 = %(direction)sdirection ? dx1 / det : -dx1 / det;
const double n%(restriction)s1 = %(direction)sdirection ? -dx0 / det : dx0 / det;"""

_facet_normal_3D = """\
// Compute facet normals from the facet scale factor constants
const double n%(restriction)s0 = %(direction)sdirection ? a0 / det : -a0 / det;
const double n%(restriction)s1 = %(direction)sdirection ? a1 / det : -a1 / det;
const double n%(restriction)s2 = %(direction)sdirection ? a2 / det : -a2 / det;"""

evaluate_basis_dof_map = """\
unsigned int element = 0;
unsigned int tmp = 0;
for (unsigned int j = 0; j < %d; j++)
{
  if (tmp +  dofs_per_element[j] > i)
  {
    i -= tmp;
    element = element_types[j];
    break;
  }
  else
    tmp += dofs_per_element[j];
}"""

combinations_snippet = """\
// Declare pointer to two dimensional array that holds combinations of derivatives and initialise
unsigned int **%(combinations)s = new unsigned int *[%(num_derivatives)s];
for (unsigned int row = 0; row < %(num_derivatives)s; row++)
{
  %(combinations)s[row] = new unsigned int [%(n)s];
  for (unsigned int col = 0; col < %(n)s; col++)
    %(combinations)s[row][col] = 0;
}

// Generate combinations of derivatives
for (unsigned int row = 1; row < %(num_derivatives)s; row++)
{
  for (unsigned int num = 0; num < row; num++)
  {
    for (unsigned int col = %(n)s-1; col+1 > 0; col--)
    {
      if (%(combinations)s[row][col] + 1 > %(topological_dimension-1)s)
        %(combinations)s[row][col] = 0;
      else
      {
        %(combinations)s[row][col] += 1;
        break;
      }
    }
  }
}"""

_transform_interval_snippet = """\
// Compute inverse of Jacobian
const double %(K)s[1][1] =  {{1.0 / J_00}};

// Declare transformation matrix
// Declare pointer to two dimensional array and initialise
double **%(transform)s = new double *[%(num_derivatives)s];

for (unsigned int j = 0; j < %(num_derivatives)s; j++)
{
  %(transform)s[j] = new double [%(num_derivatives)s];
  for (unsigned int k = 0; k < %(num_derivatives)s; k++)
    %(transform)s[j][k] = 1;
}

// Construct transformation matrix
for (unsigned int row = 0; row < %(num_derivatives)s; row++)
{
  for (unsigned int col = 0; col < %(num_derivatives)s; col++)
  {
    for (unsigned int k = 0; k < %(n)s; k++)
      %(transform)s[row][col] *= %(K)s[%(combinations)s[col][k]][%(combinations)s[row][k]];
  }
}"""

_transform_triangle_snippet = """\
// Compute inverse of Jacobian
const double %(K)s[2][2] =  {{J_11 / detJ, -J_01 / detJ}, {-J_10 / detJ, J_00 / detJ}};

// Declare transformation matrix
// Declare pointer to two dimensional array and initialise
double **%(transform)s = new double *[%(num_derivatives)s];

for (unsigned int j = 0; j < %(num_derivatives)s; j++)
{
  %(transform)s[j] = new double [%(num_derivatives)s];
  for (unsigned int k = 0; k < %(num_derivatives)s; k++)
    %(transform)s[j][k] = 1;
}

// Construct transformation matrix
for (unsigned int row = 0; row < %(num_derivatives)s; row++)
{
  for (unsigned int col = 0; col < %(num_derivatives)s; col++)
  {
    for (unsigned int k = 0; k < %(n)s; k++)
      %(transform)s[row][col] *= %(K)s[%(combinations)s[col][k]][%(combinations)s[row][k]];
  }
}"""

_transform_tetrahedron_snippet = """\
// Compute inverse of Jacobian
const double %(K)s[3][3] =\
{{d00 / detJ, d10 / detJ, d20 / detJ},\
 {d01 / detJ, d11 / detJ, d21 / detJ},\
 {d02 / detJ, d12 / detJ, d22 / detJ}};

// Declare transformation matrix
// Declare pointer to two dimensional array and initialise
double **%(transform)s = new double *[%(num_derivatives)s];

for (unsigned int j = 0; j < %(num_derivatives)s; j++)
{
  %(transform)s[j] = new double [%(num_derivatives)s];
  for (unsigned int k = 0; k < %(num_derivatives)s; k++)
    %(transform)s[j][k] = 1;
}

// Construct transformation matrix
for (unsigned int row = 0; row < %(num_derivatives)s; row++)
{
  for (unsigned int col = 0; col < %(num_derivatives)s; col++)
  {
    for (unsigned int k = 0; k < %(n)s; k++)
      %(transform)s[row][col] *= %(K)s[%(combinations)s[col][k]][%(combinations)s[row][k]];
  }
}"""


# Codesnippets used in evaluate_dof
_map_onto_physical_1D = """\
// Evaluate basis functions for affine mapping
const double w0 = 1.0 - X_%(i)d[%(j)s][0];
const double w1 = X_%(i)d[%(j)s][0];

// Compute affine mapping y = F(X)
y[0] = w0*x[0][0] + w1*x[1][0];"""

_map_onto_physical_2D = """\
// Evaluate basis functions for affine mapping
const double w0 = 1.0 - X_%(i)d[%(j)s][0] - X_%(i)d[%(j)s][1];
const double w1 = X_%(i)d[%(j)s][0];
const double w2 = X_%(i)d[%(j)s][1];

// Compute affine mapping y = F(X)
y[0] = w0*x[0][0] + w1*x[1][0] + w2*x[2][0];
y[1] = w0*x[0][1] + w1*x[1][1] + w2*x[2][1];"""

_map_onto_physical_3D = """\
// Evaluate basis functions for affine mapping
const double w0 = 1.0 - X_%(i)d[%(j)s][0] - X_%(i)d[%(j)s][1] - X_%(i)d[%(j)s][2];
const double w1 = X_%(i)d[%(j)s][0];
const double w2 = X_%(i)d[%(j)s][1];
const double w3 = X_%(i)d[%(j)s][2];

// Compute affine mapping y = F(X)
y[0] = w0*x[0][0] + w1*x[1][0] + w2*x[2][0] + w3*x[3][0];
y[1] = w0*x[0][1] + w1*x[1][1] + w2*x[2][1] + w3*x[3][1];
y[2] = w0*x[0][2] + w1*x[1][2] + w2*x[2][2] + w3*x[3][2];"""


# Codesnippets used in evaluatebasis[|derivatives]
_map_coordinates_FIAT_interval = """\
// Extract vertex coordinates
const double * const * element_coordinates = c.coordinates;

// Compute Jacobian of affine map from reference cell
const double J_00 = element_coordinates[1][0] - element_coordinates[0][0];

// Get coordinates and map to the reference (FIAT) element
double x = (2.0*coordinates[0] - element_coordinates[0][0] - element_coordinates[1][0]) / J_00;"""

_map_coordinates_FIAT_triangle = """\
// Extract vertex coordinates
const double * const * element_coordinates = c.coordinates;

// Compute Jacobian of affine map from reference cell
const double J_00 = element_coordinates[1][0] - element_coordinates[0][0];
const double J_01 = element_coordinates[2][0] - element_coordinates[0][0];
const double J_10 = element_coordinates[1][1] - element_coordinates[0][1];
const double J_11 = element_coordinates[2][1] - element_coordinates[0][1];

// Compute determinant of Jacobian
const double detJ = J_00*J_11 - J_01*J_10;

// Compute inverse of Jacobian
const double Jinv_00 =  J_11 / detJ;
const double Jinv_01 = -J_01 / detJ;
const double Jinv_10 = -J_10 / detJ;
const double Jinv_11 =  J_00 / detJ;

// Compute constants
const double C0 = element_coordinates[1][0] + element_coordinates[2][0];
const double C1 = element_coordinates[1][1] + element_coordinates[2][1];

// Get coordinates and map to the reference (FIAT) element
double x = (J_01*C1 - J_11*C0 + 2.0*J_11*coordinates[0] - 2.0*J_01*coordinates[1]) / detJ;
double y = (J_10*C0 - J_00*C1 - 2.0*J_10*coordinates[0] + 2.0*J_00*coordinates[1]) / detJ;"""

_map_coordinates_FIAT_tetrahedron = """\
// Extract vertex coordinates
const double * const * element_coordinates = c.coordinates;

// Compute Jacobian of affine map from reference cell
const double J_00 = element_coordinates[1][0] - element_coordinates[0][0];
const double J_01 = element_coordinates[2][0] - element_coordinates[0][0];
const double J_02 = element_coordinates[3][0] - element_coordinates[0][0];
const double J_10 = element_coordinates[1][1] - element_coordinates[0][1];
const double J_11 = element_coordinates[2][1] - element_coordinates[0][1];
const double J_12 = element_coordinates[3][1] - element_coordinates[0][1];
const double J_20 = element_coordinates[1][2] - element_coordinates[0][2];
const double J_21 = element_coordinates[2][2] - element_coordinates[0][2];
const double J_22 = element_coordinates[3][2] - element_coordinates[0][2];

// Compute sub determinants
const double d00 = J_11*J_22 - J_12*J_21;
const double d01 = J_12*J_20 - J_10*J_22;
const double d02 = J_10*J_21 - J_11*J_20;

const double d10 = J_02*J_21 - J_01*J_22;
const double d11 = J_00*J_22 - J_02*J_20;
const double d12 = J_01*J_20 - J_00*J_21;

const double d20 = J_01*J_12 - J_02*J_11;
const double d21 = J_02*J_10 - J_00*J_12;
const double d22 = J_00*J_11 - J_01*J_10;

// Compute determinant of Jacobian
double detJ = J_00*d00 + J_10*d10 + J_20*d20;

// Compute inverse of Jacobian
const double Jinv_00 = d00 / detJ;
const double Jinv_01 = d10 / detJ;
const double Jinv_02 = d20 / detJ;
const double Jinv_10 = d01 / detJ;
const double Jinv_11 = d11 / detJ;
const double Jinv_12 = d21 / detJ;
const double Jinv_20 = d02 / detJ;
const double Jinv_21 = d12 / detJ;
const double Jinv_22 = d22 / detJ;

// Compute constants
const double C0 = element_coordinates[3][0] + element_coordinates[2][0] \\
                + element_coordinates[1][0] - element_coordinates[0][0];
const double C1 = element_coordinates[3][1] + element_coordinates[2][1] \\
                + element_coordinates[1][1] - element_coordinates[0][1];
const double C2 = element_coordinates[3][2] + element_coordinates[2][2] \\
                + element_coordinates[1][2] - element_coordinates[0][2];

// Get coordinates and map to the reference (FIAT) element
double x = coordinates[0];
double y = coordinates[1];
double z = coordinates[2];

x = (2.0*d00*x + 2.0*d10*y + 2.0*d20*z - d00*C0 - d10*C1 - d20*C2) / detJ;
y = (2.0*d01*x + 2.0*d11*y + 2.0*d21*z - d01*C0 - d11*C1 - d21*C2) / detJ;
z = (2.0*d02*x + 2.0*d12*y + 2.0*d22*z - d02*C0 - d12*C1 - d22*C2) / detJ;"""


# Mappings to code snippets used by format

jacobian = {1: _jacobian_1D, 2: _jacobian_2D, 3: _jacobian_3D}

inverse_jacobian = {1: _inverse_jacobian_1D,
                    2: _inverse_jacobian_2D,
                    3: _inverse_jacobian_3D}

facet_determinant = {1: _facet_determinant_1D,
                     2: _facet_determinant_2D,
                     3: _facet_determinant_3D}

map_onto_physical = {1: _map_onto_physical_1D,
                     2: _map_onto_physical_2D,
                     3: _map_onto_physical_3D}

fiat_coordinate_map = {"interval": _map_coordinates_FIAT_interval,
                       "triangle": _map_coordinates_FIAT_triangle,
                       "tetrahedron": _map_coordinates_FIAT_tetrahedron}

transform_snippet = {"interval": _transform_interval_snippet,
                     "triangle": _transform_triangle_snippet,
                     "tetrahedron": _transform_tetrahedron_snippet}

normal_direction = {1: _normal_direction_1D,
                    2: _normal_direction_2D,
                    3: _normal_direction_3D}

facet_normal = {1: _facet_normal_1D,
                2: _facet_normal_2D,
                3: _facet_normal_3D}


# FIXME: Remove: These seem to be unused

# _map_coordinates_1D = _jacobian_1D + """\

# // Get coordinates and map to the UFC reference element
# double x = (coordinates[0] - element_coordinates[0][0]) / J_00;"""

# _map_coordinates_2D = _jacobian_2D + _inverse_jacobian_2D + """\

# // Get coordinates and map to the UFC reference element
# double x = (element_coordinates[0][1]*element_coordinates[2][0] -\\
#             element_coordinates[0][0]*element_coordinates[2][1] +\\
#             J_11*coordinates[0] - J_01*coordinates[1]) / detJ;
# double y = (element_coordinates[1][1]*element_coordinates[0][0] -\\
#             element_coordinates[1][0]*element_coordinates[0][1] -\\
#             J_10*coordinates[0] + J_00*coordinates[1]) / detJ;"""

# _map_coordinates_3D = _jacobian_3D + _inverse_jacobian_3D + """\

# // Compute constants
# const double C0 = d00*(element_coordinates[0][0] - element_coordinates[2][0] - element_coordinates[3][0]) \\
#                 + d10*(element_coordinates[0][1] - element_coordinates[2][1] - element_coordinates[3][1]) \\
#                 + d20*(element_coordinates[0][2] - element_coordinates[2][2] - element_coordinates[3][2]);

# const double C1 = d01*(element_coordinates[0][0] - element_coordinates[1][0] - element_coordinates[3][0]) \\
#                 + d11*(element_coordinates[0][1] - element_coordinates[1][1] - element_coordinates[3][1]) \\
#                 + d21*(element_coordinates[0][2] - element_coordinates[1][2] - element_coordinates[3][2]);

# const double C2 = d02*(element_coordinates[0][0] - element_coordinates[1][0] - element_coordinates[2][0]) \\
#                 + d12*(element_coordinates[0][1] - element_coordinates[1][1] - element_coordinates[2][1]) \\
#                 + d22*(element_coordinates[0][2] - element_coordinates[1][2] - element_coordinates[2][2]);

# // Get coordinates and map to the UFC reference element
# double x = (C0 + d00*coordinates[0] + d10*coordinates[1] + d20*coordinates[2]) / detJ;
# double y = (C1 + d01*coordinates[0] + d11*coordinates[1] + d21*coordinates[2]) / detJ;
# double z = (C2 + d02*coordinates[0] + d12*coordinates[1] + d22*coordinates[2]) / detJ;"""

# map_coordinates = {"interval": _map_coordinates_1D,
#                    "triangle": _map_coordinates_2D,
#                    "tetrahedron": _map_coordinates_3D}



# cell_integral_call = """\
# %(reset_tensor)s

# tabulate_tensor_tensor(A, w, c);
# tabulate_tensor_quadrature(A, w, c);"""

# exterior_facet_integral_call = """\
# %(reset_tensor)s

# tabulate_tensor_tensor(A, w, c, facet);
# tabulate_tensor_quadrature(A, w, c, facet);"""

# interior_facet_integral_call = """\
# %(reset_tensor)s

# tabulate_tensor_tensor(A, w, c0, c1, facet0, facet1);
# tabulate_tensor_quadrature(A, w, c0, c1, facet0, facet1);"""

