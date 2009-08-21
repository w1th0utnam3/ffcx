"Code generator for quadrature representation."

__author__ = "Kristian B. Oelgaard (k.b.oelgaard@tudelft.nl)"
__date__ = "2009-01-07 -- 2009-08-08"
__copyright__ = "Copyright (C) 2009 Kristian B. Oelgaard"
__license__  = "GNU GPL version 3 or any later version"

# Python modules.
from numpy import shape

# FFC code generation modules.
from ffc.compiler.codeutils import tabulate_matrix, IndentControl

# FFC fem module.
from ffc.fem.createelement import create_element

# FFC common modules.
from ffc.common.log import debug, info

# Utility and optimisation functions for quadraturegenerator.
from quadraturegenerator_utils import generate_loop
from quadraturetransformer import generate_code, QuadratureTransformer

from optimisedquadraturetransformer import generate_code as generate_code_opt
from optimisedquadraturetransformer import QuadratureTransformerOpt
from symbolics import generate_aux_constants

# FFC format modules.
from ffc.compiler.removeunused import remove_unused

# UFL modules.
from ufl.classes import Measure
from ufl.algorithms.analysis import extract_unique_elements
from ufl.algorithms.printing import tree_format

#class QuadratureGenerator(CodeGenerator):
class QuadratureGenerator:
    "Code generator for quadrature representation."

    def __init__(self, options):
        "Constructor"

        if options["optimize"]:
            # These options results in fast code, but compiles slower and there
            # might still be bugs.
            self.optimise_options = {"non zero columns": True,
                                     "ignore ones": True,
                                     "remove zero terms": True,
                                     "simplify expressions": True,
                                     "ignore zero tables": True}
        else:
            # These options should be safe and fast, but result in slow code.
            self.optimise_options = {"non zero columns": False,
                                     "ignore ones": False,
                                     "remove zero terms": False,
                                     "simplify expressions": False,
                                     "ignore zero tables": False}

    def generate_integrals(self, form_representation, format):
        "Generate code for all integrals."

        code = {}

        # Check if code needs to be generated.
        if form_representation.num_integrals == 0:
            return {}

        info("Generating code using quadrature representation.")

        # Set represenation.
        code["representation"] = "quadrature"

        # Generate code for cell integrals.
        code.update(self.generate_cell_integrals(form_representation, format))

        # Generate code for exterior facet integrals.
        code.update(self.generate_exterior_facet_integrals(form_representation, format))
        
        # Generate code for interior facet integrals.
        code.update(self.generate_interior_facet_integrals(form_representation, format))

        return code

    def generate_cell_integrals(self, form_representation, format):
        code = {}
        if not form_representation.cell_integrals:
            return code

        # Create transformer.
        if self.optimise_options["simplify expressions"]:
            transformer = QuadratureTransformerOpt(form_representation, Measure.CELL,\
                                                self.optimise_options, format)
        else:
            transformer = QuadratureTransformer(form_representation, Measure.CELL,\
                                                self.optimise_options, format)

        # Generate code for cell integral.
        info("\nGenerating code for cell integrals.")
        for subdomain, integrals in form_representation.cell_integrals.items():
            transformer.reset()
            code[("cell_integral", subdomain)] =\
                 self.generate_cell_integral(form_representation, transformer, integrals, format)
        return code

    def generate_exterior_facet_integrals(self, form_representation, format):
        code = {}
        if not form_representation.exterior_facet_integrals:
            return code

        # Create transformer.
        if self.optimise_options["simplify expressions"]:
            transformer = QuadratureTransformerOpt(form_representation, Measure.EXTERIOR_FACET,\
                                                self.optimise_options, format)
        else:
            transformer = QuadratureTransformer(form_representation, Measure.EXTERIOR_FACET,\
                                                self.optimise_options, format)

        # Generate code for cell integral.
        info("\nGenerating code for exterior facet integrals.")
        for subdomain, integrals in form_representation.exterior_facet_integrals.items():
            transformer.reset()
            code[("exterior_facet_integral", subdomain)] =\
                 self.generate_exterior_facet_integral(form_representation, transformer, integrals, format)
        return code

    def generate_interior_facet_integrals(self, form_representation, format):
        code = {}
        if not form_representation.interior_facet_integrals:
            return code

        # Create transformer.
        if self.optimise_options["simplify expressions"]:
            transformer = QuadratureTransformerOpt(form_representation, Measure.INTERIOR_FACET,\
                                                self.optimise_options, format)
        else:
            transformer = QuadratureTransformer(form_representation, Measure.INTERIOR_FACET,\
                                                self.optimise_options, format)

        # Generate code for cell integral.
        info("\nGenerating code for interior facet integrals.")
        for subdomain, integrals in form_representation.interior_facet_integrals.items():
            transformer.reset()
            code[("interior_facet_integral", subdomain)] =\
                 self.generate_interior_facet_integral(form_representation, transformer, integrals, format)
        return code

    def generate_cell_integral(self, form_representation, transformer, integrals, format):
        """Generate dictionary of code for cell integrals on a given subdomain
        from the given form representation according to the given format."""

        debug("\nQG, cell_integral, integrals:\n" + str(integrals))

        # Object to control the code indentation.
        Indent = IndentControl()

        # Update treansformer with facets.
        transformer.update_facets(None, None)

        # Generate element code + set of used geometry terms.
        element_code, members_code, num_ops =\
          self.__generate_element_tensor(form_representation, transformer,\
                                         integrals, Indent, format)
        # Get Jacobian snippet.
        # FIXME: This will most likely have to change if we support e.g., 2D elements in 3D space.
        jacobi_code = [format["generate jacobian"](transformer.geo_dim, "cell")]

        # After we have generated the element code we can remove the unused
        # transformations and tabulate the used psi tables and weights.

        # Remove unused declarations.
        code = self.__remove_unused(jacobi_code, transformer.trans_set, format)

        # Tabulate weights at quadrature points.
        code += self.__tabulate_weights(transformer, Indent, format)

        # Tabulate values of basis functions and their derivatives.
        code += self.__tabulate_psis(transformer, Indent, format)

        # Create the constant geometry declarations (only generated if simplify expressions are enabled).
        geo_ops, geo_code = generate_aux_constants(transformer.geo_consts, format["geometry tensor"], format["const float declaration"])
        if geo_code:
            num_ops += geo_ops
            code += ["", format["comment"]("Number of operations to compute geometry constants: %d" %geo_ops)]
            code += geo_code

        # Add element code.
        code += ["", format["comment"]("Compute element tensor using UFL quadrature representation"),\
                 format["comment"]("Optimisations: %s" % ", ".join([str(i) for i in self.optimise_options.items()])),\
                 format["comment"]("Total number of operations to compute element tensor: %d" %num_ops)]
        code += element_code

        info("Number of operations to compute tensor: %d" % num_ops)

        return {"tabulate_tensor": code, "members": members_code}


    def generate_exterior_facet_integral(self, form_representation, transformer, integrals, format):
        """Generate dictionary of code for exterior facet integral from the given
        form representation according to the given format."""

        debug("\nQG, exterior_facet_integral, integral:\n" + str(integrals))

        # Object to control the code indentation.
        Indent = IndentControl()

        num_facets = form_representation.form_data.num_facets
        cases = [None for i in range(num_facets)]
        for i in range(num_facets):

            # Update treansformer with facets.
            transformer.update_facets(i, None)
            
            case = [format["block begin"]]
            c, members_code, num_ops =\
                self.__generate_element_tensor(form_representation, transformer,\
                                               integrals, Indent, format)

            case += [format["comment"]("Total number of operations to compute element tensor (from this point): %d" %num_ops)] + c
            case += [format["block end"]]
            cases[i] = case
            info("Number of operations to compute tensor for facet %d: %d" % (i, num_ops))

        # Get Jacobian snippet.
        # FIXME: This will most likely have to change if we support e.g., 2D elements in 3D space.
        jacobi_code = [format["generate jacobian"](transformer.geo_dim, "exterior facet")]

        # After we have generated the element code for all facets we can remove
        # the unused transformations and tabulate the used psi tables and weights.

        # Remove unused declarations.
        common = self.__remove_unused(jacobi_code, transformer.trans_set, format)

        # Tabulate weights at quadrature points.
        common += self.__tabulate_weights(transformer, Indent, format)

        # Tabulate values of basis functions and their derivatives.
        common += self.__tabulate_psis(transformer, Indent, format)

        # Create the constant geometry declarations (only generated if simplify expressions are enabled).
        geo_ops, geo_code = generate_aux_constants(transformer.geo_consts, format["geometry tensor"], format["const float declaration"])
        if geo_code:
            num_ops += geo_ops
            common += ["", format["comment"]("Number of operations to compute geometry constants: %d" %geo_ops)]
            common += [format["comment"]("Should be added to total operation count.")]
            common += geo_code
            info("Number of operations to compute geometry terms: %s, should be added to facet count." % geo_ops)

        # Add comments.
        common += ["", format["comment"]("Compute element tensor using UFL quadrature representation"),\
                 format["comment"]("Optimisations: %s" % ", ".join([str(i) for i in self.optimise_options.items()]))]

        return {"tabulate_tensor": (common, cases), "members": members_code}
    
    def generate_interior_facet_integral(self, form_representation, transformer, integrals, format):
        """Generate dictionary of code for interior facet integral from the given
        form representation according to the given format."""

        debug("\nQG, interior_facet_integral, integral:\n" + str(integrals))

        # Object to control the code indentation.
        Indent = IndentControl()
        num_facets = form_representation.form_data.num_facets
        cases = [[None for j in range(num_facets)] for i in range(num_facets)]
        for i in range(num_facets):
            for j in range(num_facets):
                # Update treansformer with facets.
                transformer.update_facets(i, j)

                case = [format["block begin"]]
                c, members_code, num_ops =\
                    self.__generate_element_tensor(form_representation, transformer,\
                                                   integrals, Indent, format, interior=True)
                case += [format["comment"]("Total number of operations to compute element tensor (from this point): %d" %num_ops)] + c
                case += [format["block end"]]
                cases[i][j] = case
                info("Number of operations to compute tensor for facets (%d, %d): %d" % (i, j, num_ops))

        # Get Jacobian snippet.
        # FIXME: This will most likely have to change if we support e.g., 2D elements in 3D space.
        jacobi_code = [format["generate jacobian"](transformer.geo_dim, "interior facet")]

        # After we have generated the element code for all facets we can remove
        # the unused transformations and tabulate the used psi tables and weights.

        # Remove unused declarations.
        common = self.__remove_unused(jacobi_code, transformer.trans_set, format)

        # Tabulate weights at quadrature points.
        common += self.__tabulate_weights(transformer, Indent, format)

        # Tabulate values of basis functions and their derivatives.
        common += self.__tabulate_psis(transformer, Indent, format)

        # Create the constant geometry declarations (only generated if simplify expressions are enabled).
        geo_ops, geo_code = generate_aux_constants(transformer.geo_consts, format["geometry tensor"], format["const float declaration"])
        if geo_code:
            num_ops += geo_ops
            common += ["", format["comment"]("Number of operations to compute geometry constants: %d" %geo_ops)]
            common += [format["comment"]("Should be added to total operation count.")]
            common += geo_code
            info("Number of operations to compute geometry terms: %s, should be added to facet count." % geo_ops)

        # Add comments.
        common += ["", format["comment"]("Compute element tensor using UFL quadrature representation"),\
                 format["comment"]("Optimisations: %s" % ", ".join([str(i) for i in self.optimise_options.items()]))]

        return {"tabulate_tensor": (common, cases), "constructor":"// Do nothing", "members":members_code}

    def __generate_element_tensor(self, form_representation, transformer, integrals, Indent, format, interior=False):
        "Construct quadrature code for element tensors."

        # Prefetch formats to speed up code generation.
        format_comment      = format["comment"]
        format_ip           = format["integration points"]

        # Initialise return values.
        element_code     = []
        tensor_ops_count = 0
        # TODO: The members_code was used when I generated the load_table.h
        # file which could load tables of basisfunction. This feature has not
        # been reimplemented. However, with the new design where we only
        # tabulate unique tables (and only non-zero entries) it doesn't seem to
        # be necessary. Should it be deleted?
        members_code = ""

        # We receive a dictionary {num_points: integral,}.
        # Loop points and integrals.
        for points, integral in integrals.items():
            debug("Looping points: " + str(points))
            debug("integral: " + str(integral))
            debug("\nIntegral tree_format: " + str(tree_format(integral)))

            ip_code = ["", Indent.indent(format_comment\
                ("Loop quadrature points for integral"))]

            # Update transformer to the current number of quadrature points.
            transformer.update_points(points)

            # Generate code for integrand and get number of operations.
            if self.optimise_options["simplify expressions"]:
                integral_code, num_ops =\
                    generate_code_opt(integral.integrand(), transformer, Indent, format, interior)
            else:
                integral_code, num_ops =\
                    generate_code(integral.integrand(), transformer, Indent, format, interior)

            # Get number of operations to compute entries for all terms when
            # looping over all IPs and update tensor count.
            num_operations = num_ops*points
            tensor_ops_count += num_operations

            ip_code.append(format_comment\
                ("Number of operations to compute element tensor for following IP loop = %d" %(num_operations)) )

            # Loop code over all IPs.
            if integral_code:
                if points > 1:
                    ip_code += generate_loop(integral_code, [(format_ip, 0, points)], Indent, format)
                else:
                    ip_code.append(format_comment("Only 1 integration point, omitting IP loop."))
                    ip_code += integral_code

            # Add integration points code to element code.
            element_code += ip_code

        return (element_code, members_code, tensor_ops_count)


    def __tabulate_weights(self, transformer, Indent, format):
        "Generate table of quadrature weights."

        # Prefetch formats to speed up code generation.
        format_float    = format["floating point"]
        format_table    = format["table declaration"]
        format_block    = format["block"]
        format_sep      = format["separator"]
        format_weight   = format["weight"]
        format_array    = format["array access"]
        format_group    = format["grouping"]

        code = ["", Indent.indent(format["comment"]("Array of quadrature weights"))]

        # Loop tables of weights and create code.
        for num_points in transformer.used_weights:
            weights, points = transformer.quadrature_weights[num_points]

            # FIXME: For now, raise error if we don't have weights.
            # We might want to change this later.
            if not weights.any():
                raise RuntimeError(weights, "No weights.")

            # Create name and value for weight.
            name = format_table + format_weight(num_points)
            value = format_float(weights[0])
            if len(weights) > 1:
                name += format_array(str(num_points))
                value = format_block(format_sep.join([format_float(w)\
                                                      for w in weights]))
            code += [(Indent.indent(name), value)]

            # Tabulate the quadrature points (uncomment for different options).
            # 1) Tabulate the points as: p0, p1, p2, with p0 = (x0, y0, z0) etc.
            # Use format_float to format the value (enable variable precision).
            formatted_points = [format_group(format_sep.join([format_float(val)\
                                for val in point])) for point in points]

            # Create comment.
            comment = "Quadrature points on the UFC reference element: " \
                      + format_sep.join(formatted_points)
            code += [Indent.indent(format["comment"](comment))]

            # 2) Tabulate the coordinates of the points p0, p1, p2 etc.
            #    X: x0, x1, x2
            #    Y: y0, y1, y2
            #    Z: z0, z1, z2
#            comment = "Quadrature coordinates on the UFC reference element: "
#            code += [Indent.indent(format["comment"](comment))]

#            # All points have the same number of coordinates.
#            num_coord = len(points[0])

#            # All points have x-coordinates.
#            xs = [format_float(p[0]) for p in points]
#            comment = "X: " + format_sep.join(xs)
#            code += [Indent.indent(format["comment"](comment))]

#            ys = []
#            zs = []
#            # Tabulate y-coordinate if we have 2 or more coordinates.
#            if num_coord >= 2:
#                ys = [format_float(p[1]) for p in points]
#                comment = "Y: " + format_sep.join(ys)
#                code += [Indent.indent(format["comment"](comment))]
#            # Only tabulate z-coordinate if we have 3 coordinates.
#            if num_coord == 3:
#                zs = [format_float(p[2]) for p in points]
#                comment = "Z: " + format_sep.join(zs)
#                code += [Indent.indent(format["comment"](comment))]

            code += [""]

        return code

    def __tabulate_psis(self, transformer, Indent, format):
        "Tabulate values of basis functions and their derivatives at quadrature points."

        # Prefetch formats to speed up code generation.
        format_comment    = format["comment"]
        format_block      = format["block"]
        format_table      = format["table declaration"]
        format_matrix     = format["matrix access"]
        format_array      = format["array access"]
        format_const_uint = format["static const uint declaration"]
        format_nzcolumns  = format["nonzero columns"]
        format_sep        = format["separator"]

        # FIXME: Check if we can simplify the tabulation

        code = []
        code += [Indent.indent(format_comment("Value of basis functions at quadrature points.") )]

        inv_name_map = transformer.name_map
        tables = transformer.unique_tables

        # Get list of non zero columns, if we ignore ones ignore columns with one component.
        if self.optimise_options["ignore ones"]:
            nzcs = [val[1] for key, val in inv_name_map.items()\
                                           if val[1] and len(val[1][1]) > 1]
        else:
            nzcs = [val[1] for key, val in inv_name_map.items()\
                                           if val[1]]

        # TODO: Do we get arrays that are not unique?
        new_nzcs = []
        for nz in nzcs:
            # Only get unique arrays.
            if not nz in new_nzcs:
                new_nzcs.append(nz)

        # Construct name map.
        name_map = {}
        if inv_name_map:
            for name in inv_name_map:
                if inv_name_map[name][0] in name_map:
                    name_map[inv_name_map[name][0]].append(name)
                else:
                    name_map[inv_name_map[name][0]] = [name]

        # Loop items in table and tabulate.
        for name in transformer.used_psi_tables:
            # Only proceed if values are still used (if they're not remapped).
            vals = tables[name]
            if not vals == None:
                # Add declaration to name.
                ip, dofs = shape(vals)
                decl_name = format_table + name + format_matrix(ip, dofs)

                # Generate array of values.
                value = tabulate_matrix(vals, format)
                code += [(Indent.indent(decl_name), Indent.indent(value)), ""]

            # Tabulate non-zero indices.
            if self.optimise_options["non zero columns"]:
                if name in name_map:
                    for n in name_map[name]:
                        if inv_name_map[n][1] and inv_name_map[n][1] in new_nzcs:
                            i, cols = inv_name_map[n][1]
                            if not i in transformer.used_nzcs:
                                continue
                            code += [Indent.indent(format_comment("Array of non-zero columns") )]
                            value = format_block(format_sep.join(["%d" %c for c in list(cols)]))
                            name_col = format_const_uint + format_nzcolumns(i) + format_array(len(cols))
                            code += [(Indent.indent(name_col), value)]

                            # Remove from list of columns.
                            new_nzcs.remove(inv_name_map[n][1])
        return code

    def __remove_unused(self, code, trans_set, format):
        "Remove unused variables so that the compiler will not complain."

        # Normally, the removal of unused variables should happen at the
        # formatting stage, but since the code for the tabulate_tensor()
        # function may grow to considerable size, we make an exception and
        # remove unused variables here when we know the names of the used
        # variables. No searching necessary and much, much, much faster.

        if code:
            # Generate body of code, using the format.
            lines = format["generate body"](code)

            # Generate auxiliary code line that uses all members of the set
            # (to trick remove_unused).
            line_set = format["add equal"]("A", format["multiply"](trans_set))
            lines += "\n" + line_set

            # Remove unused Jacobi declarations.
            code = remove_unused(lines)

            # Delete auxiliary line.
            code = code.replace("\n" + line_set, "")

            return [code]
        else:
            return code
