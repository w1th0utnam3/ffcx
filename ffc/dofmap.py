__author__ = "Anders Logg (logg@simula.no)"
__date__ = "2007-01-24"
__copyright__ = "Copyright (C) 2007-2008 Anders Logg"
__license__  = "GNU GPL version 3 or any later version"

# Modified by Marie E. Rognes (meg@math.uio.no), 2007
# Modified by Kristian Oelgaard, 2007 - 2009
# Last changed: 2009-12-09

# FFC modules
from utils import pick_first
from utils import compute_permutations
from log import error
from finiteelement import FiniteElement
from quadratureelement import QuadratureElement

class DofMap:
    """A DofMap represents a description of the degrees of a freedom
    of a finite element space, from which the mapping from local to
    global degrees of freedom can be computed."""

    def __init__(self, element):
        "Create dof map from given finite element"

        # Get entity dofs and dof representation from element
        entity_dofs = element.entity_dofs()

        # Generate dof map data
        self.__signature           = "FFC dof map for " + repr(element)
        self.__local_dimension     = element.space_dimension()
        self.__geometric_dimension = element.cell().geometric_dimension()
        self.__entity_dofs         = entity_dofs
        self.__num_dofs_per_dim    = self.__compute_num_dofs_per_dim(entity_dofs)
        self.__num_facet_dofs      = self.__compute_num_facet_dofs(entity_dofs, element.cell().domain())
        self.__dof_entities        = self.__compute_dof_entities(entity_dofs)
        self.__incidence           = self.__compute_incidence(element.cell().domain())
        self.__dof_maps            = self.__compute_dof_maps(element)
        self.__element             = element

    def signature(self):
        "Return a string identifying the dof map"
        return self.__signature

    def local_dimension(self):
        "Return the dimension of the local finite element function space"
        return self.__local_dimension

    def geometric_dimension(self):
        "Return the geometric dimension of the finite element domain"
        return self.__geometric_dimension

    def entity_dofs(self):
        """Return a dictionary mapping the mesh entities of the
        reference cell to the degrees of freedom associated with the
        entity"""
        return self.__entity_dofs

    def num_facet_dofs(self):
        "Return the number of dofs on each cell facet"
        return self.__num_facet_dofs

    def get_num_of_points(self):
        "Return the number of points associated with each dof"
        return [len(dof.points) for dof in self.dual_basis()]

    def get_max_num_of_points(self):
        "Return the maximal number of points associated with the dofs"
        return max(self.get_num_of_points())
       
    def dof_coordinates(self):
        "Return the coordinates associated with each dof"
        # FIXME meg: Now returns the first coordinate associated with
        # each dof... for the sake of the codegeneration for
        # tabulate_coordinates!
        return [dof.points[0] for dof in self.dual_basis()]

    def num_dofs_per_dim(self, sub_dof_map=None):
        "Return the number of dofs associated with each topological dimension for sub dof map or total"
        if sub_dof_map == None:
            D = max(self.__entity_dofs[0])
            num_dofs_per_dim = (D + 1)*[0]
            for sub_num_dofs_per_dim in self.__num_dofs_per_dim:
                for dim in sub_num_dofs_per_dim:
                    num_dofs_per_dim[dim] += sub_num_dofs_per_dim[dim]
            return num_dofs_per_dim
        else:
            return self.__num_dofs_per_dim[sub_dof_map]

    def dof_entities(self):
        "Return a list of which entities are associated with each dof"
        return self.__dof_entities

    def incidence(self):
        "Return a dictionary of which entities are incident with which"
        return self.__incidence

    def num_sub_dof_maps(self):
        "Return the number of sub dof maps"
        return len(self.__dof_maps)

    def sub_dof_map(self, i):
        "Return sub dof map i"
        if len(self.__dof_maps) > 0:
            return self.__dof_maps[i]
        else:
            return None

    def element(self):
        "Return the finite element associated with the dof map"
        return self.__element

    def dual_basis(self):
        """Return the representation of the dual basis for the element
        associated with the DofMap"""
        return self.element().dual_basis()

    def __compute_num_dofs_per_dim(self, entity_dofs):
        "Compute the number of dofs associated with each topological dimension"
        num_dofs_per_dim = []
        for sub_entity_dofs in entity_dofs:
            sub_num_dofs_per_dim = {}
            for dim in sub_entity_dofs:
                num_dofs = [len(sub_entity_dofs[dim][entity]) for entity in sub_entity_dofs[dim]]
                if dim in sub_num_dofs_per_dim:
                    sub_num_dofs_per_dim[dim] += pick_first(num_dofs)
                else:
                    sub_num_dofs_per_dim[dim] = pick_first(num_dofs)
            num_dofs_per_dim += [sub_num_dofs_per_dim]
        return num_dofs_per_dim

    def __compute_num_facet_dofs(self, entity_dofs, cell_shape):
        "Compute the number of dofs on each cell facet"

        # Number of entites of each dimension incident with a facet
        num_facet_entities = {"interval": [1, 0], "triangle": [2, 1, 0], "tetrahedron": [3, 3, 1, 0]}

        # Get total number of dofs per dimension
        num_dofs_per_dim = self.num_dofs_per_dim()

        # Count the total
        num_facet_dofs = 0
        for dim in range(len(num_dofs_per_dim)):
            num_facet_dofs += num_facet_entities[cell_shape][dim]*num_dofs_per_dim[dim]

        return num_facet_dofs
        
    def __compute_dof_entities(self, entity_dofs):
        "Compute the entities associated with each dof"
        dof_entities = {}
        offset = 0
        for sub_entity_dofs in entity_dofs:
            for dim in sub_entity_dofs:
                for entity in sub_entity_dofs[dim]:
                    for dof in sub_entity_dofs[dim][entity]:
                        dof_entities[offset + dof] = (dim, entity)
            offset = max(dof_entities) + 1
        return dof_entities

    def __compute_incidence(self, cell_shape):
        "Compute which entities are incident with which"

        # Set topological dimension of simplex
        if cell_shape == "interval":
            D = 1
        elif cell_shape == "triangle":
            D = 2
        elif cell_shape == "tetrahedron":
            D = 3
        else:
            error("Cannot handle cell shape: " + str(cell_shape))

        # Compute the incident vertices for each entity
        sub_simplices = []
        for dim in range(D + 1):
            sub_simplices += [self.__compute_sub_simplices(D, dim)]

        # Check which entities are incident, d0 --> d1 for d0 >= d1
        incidence = {}
        for d0 in range(0, D + 1):
            for i0 in range(len(sub_simplices[d0])):
                for d1 in range(d0 + 1):
                    for i1 in range(len(sub_simplices[d1])):
                        if min([v in sub_simplices[d0][i0] for v in sub_simplices[d1][i1]]) == True:
                            incidence[((d0, i0), (d1, i1))] = True
                        else:
                            incidence[((d0, i0), (d1, i1))] = False

        return incidence

    def __compute_dof_maps(self, element):
        "Compute recursively nested dof maps"
        if isinstance(element, FiniteElement):
            return [self]
        return [DofMap(element.sub_element(i)) for i in range(element.num_sub_elements())]

    def __compute_sub_simplices(self, D, d):
        "Compute vertices for all sub simplices of dimension d (code taken from Exterior)"

        # Number of vertices
        num_vertices = D + 1

        # Special cases: d = 0 and d = D
        if d == 0:
            return [[i] for i in range(num_vertices)]
        elif d == D:
            return [range(num_vertices)]

        # Compute all permutations of num_vertices - (d + 1)
        permutations = compute_permutations(num_vertices - d - 1, num_vertices)

        # Iterate over sub simplices
        sub_simplices = []
        for i in range(len(permutations)):

            # Pick tuple i among permutations (non-incident vertices)
            remove = permutations[i]

            # Remove vertices, keeping d + 1 vertices
            vertices = [v for v in range(num_vertices) if not v in remove]
            sub_simplices += [vertices]

        return sub_simplices

    def __is_vector_lagrange(self, element):
        "Check if element is vector Lagrange element"
        if not element.family() == "Mixed":
            return False
        families = [element.sub_element(i).family() for i in range(element.num_sub_elements())]
        dimensions = [element.sub_element(i).space_dimension() for i in range(element.num_sub_elements())]
        return families[:-1] == families[1:] and \
               dimensions[:-1] == dimensions[1:]  and \
               families[0] in ["Lagrange", "Discontinuous Lagrange"]
        
    def __repr__(self):
        "Pretty print"
        return self.signature()