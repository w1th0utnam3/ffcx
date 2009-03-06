__author__ = "Anders Logg (logg@simula.no)"
__date__ = "2007-02-05 -- 2009-03-05"
__copyright__ = "Copyright (C) 2007-2009 Anders Logg"
__license__  = "GNU GPL version 3 or any later version"

# UFL modules
from ufl.algorithms import extract_monomial_form, MonomialForm
from ufl.integral import Measure

# FFC common modules
from ffc.common.log import debug, info, warning, error, begin, end, set_level, INFO

# FFC language modules
#from ffc.compiler.language.integral import *

# FFC tensor representation modules
from uflreferencetensor import ReferenceTensor
#from geometrytensor import *
#from tensorreordering import *

class TensorContraction:
    "This class represents a tensor contraction A^K = A^0 : G_K."

    def __init__(self, monomial, domain_type, facet0=None, facet1=None):
        "Create tensor contraction for given monomial."
        self.monomial = monomial
        self.A0 = ReferenceTensor(monomial, domain_type, facet0, facet1)
        self.GK = GeometryTensor(monomial)

class TensorRepresentation:
    """This class represents a given multilinear form as a tensor
    contraction, or more precisely, a sum of tensor contractions for
    each type of integral: cell, exterior facet and interior facet.

    Attributes:

        form                   - the form generating the tensor contraction
        cell_tensor            - the representation of the cell tensor
        exterior_facet_tensors - the representation of the interior facet tensors,
                                 one for each facet
        interior_facet_tensors - the representation of the exterior facet tensors,
                                 one for each facet-facet combination
    """

    def __init__(self, form):
        "Create tensor representation for given form."

        # Extract monomial representation
        monomial_form = extract_monomial_form(form)
        print "\n" + str(monomial_form)

        # Compute representation of cell tensor
        self.cell_tensor = self.__compute_cell_tensor(monomial_form)
        
        # Compute representation of exterior facet tensors
        #self.exterior_facet_tensors = self.__compute_exterior_facet_tensors(form)

        # Compute representation of interior facet tensors
        #self.interior_facet_tensors = self.__compute_interior_facet_tensors(form)
        
    def __compute_cell_tensor(self, monomial_form):
        "Compute representation of cell tensor."
        
        begin("Computing cell tensor")

        # Extract all cell integrals
        monomial_form = _extract_integrals(monomial_form, Measure.CELL)

        # Compute sum of tensor representations
        terms = _compute_terms(monomial_form, Measure.CELL, None, None)
        
        end()
        
        return terms

    def __compute_exterior_facet_tensors(self, form):
        "Compute representation of exterior facet tensors"
        debug_begin("Computing exterior facet tensors")

        # Extract monomials
        monomials = self.__extract_monomials(form, Integral.EXTERIOR_FACET)
        if len(monomials) == 0:
            debug_end()
            return []

        # Compute factorization
        factorization = self.__compute_factorization(monomials)

        # Get the number of facets
        num_facets = form.monomials[0].basisfunctions[0].element.num_facets()

        debug("Number of facets to consider: %d" % num_facets)
        
        # Compute sum of tensor representations for each facet
        terms = [None for i in range(num_facets)]
        for i in range(num_facets):
            terms[i] = self.__compute_terms(monomials, factorization, Integral.EXTERIOR_FACET, i, None)

        debug_end()
        return terms

    def __compute_interior_facet_tensors(self, form):
        "Compute representation of interior facet tensors"
        debug_begin("Computing interior facet tensors")

        # Extract monomials
        monomials = self.__extract_monomials(form, Integral.INTERIOR_FACET)
        if len(monomials) == 0:
            debug_end()
            return []

        # Compute factorization
        factorization = self.__compute_factorization(monomials)

        # Get the number of facets
        num_facets = form.monomials[0].basisfunctions[0].element.num_facets()

        debug("Number of facets to consider: %d x %d" % (num_facets, num_facets))
        
        # Compute sum of tensor representations for each facet-facet combination
        terms = [[None for j in range(num_facets)] for i in range(num_facets)]
        for i in range(num_facets):
            for j in range(num_facets):
                terms[i][j] = self.__compute_terms(monomials, factorization, Integral.INTERIOR_FACET, i, j)
                reorder_entries(terms[i][j])
                
        debug_end()
        return terms

    def __extract_monomials(self, form, integral_type):
        "Extract monomials and factorize"

        # Extract monomials of given type
        monomials = [m for m in form.monomials if m.integral.type == integral_type]
        if len(monomials) > 0:
            debug("Number of terms to consider: %d" % len(monomials))
        else:
            debug("No terms")

        return monomials

    def __compute_factorization(self, monomials):
        "Compute factorization"

        factorization = factorize(monomials)
        num_terms = sum([1 for m in factorization if m == None])
        debug("Number of terms to compute: %d" % num_terms)
        return factorization

    def __debug(self, i, facet0, facet1):
        "Fancy printing of progress"
        if facet0 == facet1 == None:
            debug("Computing tensor representation for term %d..." % i)
        elif facet1 == None:
            debug("Computing tensor representation for facet %d, term %d..." % (facet0, i))
        else:
            debug("Computing tensor representation for facets (%d, %d), term %d..." % (facet0, facet1, i))

def _extract_integrals(monomial_form, domain_type):
    "Extract subset of form matching given domain type."
    new_form = MonomialForm()
    for (integrand, measure) in monomial_form:
        if measure.domain_type() == domain_type:
            new_form.append(integrand, measure)
    return new_form

def _compute_terms(monomial_form, domain_type, facet0, facet1):
    "Compute list of tensor contraction terms for monomial form."

    # Compute terms
    terms = []
    for (integrand, measure) in monomial_form:

        # Only consider monomials of given integral type
        if not measure.domain_type() == domain_type:
            continue

        # Iterate over monomials of integrand
        for monomial in integrand.monomials:
            terms.append(TensorContraction(monomial, domain_type, facet0, facet1))

    return terms
