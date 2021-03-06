# -*- coding: utf-8 -*-
# Copyright (C) 2011-2018 Marie E. Rognes and Garth N. Wells
#
# This file is part of FFC (https://www.fenicsproject.org)
#
# SPDX-License-Identifier:    LGPL-3.0-or-later
#
# Based on original implementation by Martin Alnes and Anders Logg

# NB: generate_dolfin_namespace(...) assumes that if a coefficient has
# the same name in multiple forms, it is indeed the same coefficient:

parameters = {"use_common_coefficient_names": True}


def generate_wrappers(prefix, forms, common_function_space=False):
    """Generate complete dolfin wrapper code with given generated names.

    @param prefix:
        String, prefix for all form names
    @param forms:
        List of UFCFormNames instances or single UFCElementNames.
    @param common_function_space:
        True if common function space, otherwise False
    """

    # Tag
    code_h = "\n// DOLFIN helper functions\n"
    code_c = "\n// DOLFIN helper functions\n"

    # Typedefs for convenience factory functions
    code_h += """
// Typedefs for convenience pointers to functions (factories)
typedef dolfin_function_space* (*dolfin_function_space_factory_ptr)(void);
typedef dolfin_form* (*dolfin_form_factory_ptr)(void);

"""

    # Generate body of dolfin wrappers
    if all(isinstance(element, UFCElementNames) for element in forms):
        # NOTE: This is messy because an element doesn't (at the
        # moment) have a coordinate map
        for element in forms:
            cmap = element.coordinate_mapping_classname
            args = {
                "prefix": prefix,
                "classname": "FunctionSpace_{}".format(element.name),
                "finite_element_classname": element.element_classname,
                "dofmap_classname": element.dofmap_classname,
                "coordinate_map_classname": "create_{}".format(cmap) if cmap else "NULL"
            }
            code_h += FUNCTION_SPACE_TEMPLATE_DECL.format_map(args)
            code_c += FUNCTION_SPACE_TEMPLATE_IMPL.format_map(args)
    elif all(isinstance(form, UFCFormNames) for form in forms):
        # FIXME: Convert to dict
        # Extract (common) coefficient spaces
        assert (parameters["use_common_coefficient_names"])
        spaces = extract_coefficient_spaces(forms)

        # Generate dolfin_function_space code for common coefficient spaces
        code_h += "// Coefficient spaces helpers (number: {})\n".format(len(spaces))
        for space in spaces:
            args = {
                "prefix": prefix,
                "classname": space[0],
                "finite_element_classname": space[1],
                "dofmap_classname": space[2],
                "coordinate_map_classname": "create_{}".format(str(space[3]))
            }
            code_h += FUNCTION_SPACE_TEMPLATE_DECL.format_map(args)
            code_c += FUNCTION_SPACE_TEMPLATE_IMPL.format_map(args)

        # code_h += "\n// Form function spaces helpers (number of forms: {})\n".format(len(forms))
        for form in forms:
            code_h += "\n// Form function spaces helpers (form '{}')\n".format(form.name)
            code = generate_form(form, prefix, "Form_{}".format(form.name))
            code_h += code[0]
            code_c += code[1]

        # Generate 'top-level' typedefs (Bilinear/Linear & Test/Trial/Function)
        code_h += generate_namespace_typedefs(forms, prefix, common_function_space)
    else:
        raise TypeError("Unexpected (possibly mixed) type.")

    return code_h, code_c


def generate_namespace_typedefs(forms, prefix, common_function_space):

    # Generate typedefs as (fro, to) pairs of strings
    pairs = []

    typedefs_comment = "\n// High-level typedefs\n"

    # Add typedef for Functional/LinearForm/BilinearForm if only one
    # is present of each
    aliases = ["Functional", "LinearForm", "BilinearForm"]
    extra_aliases = {"LinearForm": "ResidualForm", "BilinearForm": "JacobianForm"}
    for rank in sorted(range(len(aliases)), reverse=True):
        forms_of_rank = [form for form in forms if form.rank == rank]
        if len(forms_of_rank) == 1:
            pairs += [("Form_{}".format(forms_of_rank[0].name), aliases[rank])]
            if aliases[rank] in extra_aliases:
                extra_alias = extra_aliases[aliases[rank]]
                pairs += [("Form_{}".format(forms_of_rank[0].name), extra_alias)]

    # Combine data to typedef code
    typedefs = "\n".join(
        "static const dolfin_form_factory_ptr {0}{1} = {0}{2};".format(prefix, fro, to)
        for (to, fro) in pairs)

    # Keepin' it simple: Add typedef for function space factory if term applies
    if common_function_space:
        for i, form in enumerate(forms):
            if form.rank:
                # FIXME: Is this naming robust?
                typedefs += "\n\nstatic const dolfin_function_space_factory_ptr {0}FunctionSpace = {0}Form_{1}_FunctionSpace_0;".format(  # noqa: E501
                    prefix, form.name)
                break

    if not typedefs:
        return typedefs_comment + "//  - None"
    return typedefs_comment + typedefs + "\n"


def generate_form(form, prefix, classname):
    """Generate dolfin wrapper code associated with a form including code
    for function spaces used in form and typedefs

    @param form:
        A UFCFormNames instance
    @param prefix
        Prefix (namespace) added to names.
    @param classname
        Name of Form class.

    """

    blocks_h = []
    blocks_c = []

    # Generate code for "Form_x_FunctionSpace_y" factories
    # FIXME: Is this always the case?
    assert (len(form.ufc_coordinate_mapping_classnames) == 1)
    for i in range(form.rank):
        args = {
            "prefix": prefix,
            "classname": "{}_FunctionSpace_{}".format(classname, i),
            "finite_element_classname": form.ufc_finite_element_classnames[i],
            "dofmap_classname": form.ufc_dofmap_classnames[i],
            "coordinate_map_classname":
            "create_{}".format(form.ufc_coordinate_mapping_classnames[0])
        }
        blocks_h += [FUNCTION_SPACE_TEMPLATE_DECL.format_map(args)]
        blocks_c += [FUNCTION_SPACE_TEMPLATE_IMPL.format_map(args)]

    # Add factory function typedefs, e.g. Form_L_FunctionSpace_1_factory = CoefficientSpace_f_factory
    blocks_h += ["// Coefficient function space typedefs for form \"{}\"".format(classname)]
    template = "static const dolfin_function_space_factory_ptr {0}{1}_FunctionSpace_{2} = {0}CoefficientSpace_{3};"
    blocks_h += [
        template.format(prefix, classname, form.rank + i, form.coefficient_names[i])
        for i in range(form.num_coefficients)
    ]
    if form.num_coefficients == 0:
        blocks_h += ["//   - None"]
    blocks_h += [""]

    # Generate Form factory
    code_h, code_c = generate_form_class(form, prefix, classname)

    # Return code
    return "\n".join(blocks_h) + code_h, "\n".join(blocks_c) + code_c


def generate_form_class(form, prefix, classname):
    """Generate dolfin wrapper code for a single Form class."""

    # Generate data for coefficient assignments
    (number, name) = generate_coefficient_map_data(form)

    # Generate typedefs for FunctionSpace subclasses for Coefficients
    typedefs = "// Typedefs (function spaces for {})\n".format(
        classname) + generate_function_space_typedefs(form, prefix, classname)

    # Wrap functions in class body
    args = {
        "prefix": prefix,
        "classname": classname,
        "ufc_form": form.ufc_form_classname,
        "coefficient_number": number,
        "coefficient_name": name,
        "typedefs": typedefs
    }

    code_h = FORM_CLASS_TEMPLATE_DECL.format_map(args)
    code_c = FORM_CLASS_TEMPLATE_IMPL.format_map(args)

    return code_h, code_c


def generate_coefficient_map_data(form):
    """Generate data for code for the functions Form::coefficient_number
    and Form::coefficient_name."""

    # Handle case of no coefficients
    if form.num_coefficients == 0:
        num = "  return -1;"
        name = "  return NULL;"
        return (num, name)

    # Otherwise create switch
    ifstr = "if "
    num = ""
    name = '  switch (i)\n  {\n'
    for i, coeff in enumerate(form.coefficient_names):
        num += '  %s(strcmp(name, "%s") == 0)\n    return %d;\n' % (ifstr, coeff, i)
        name += '  case %d:\n    return "%s";\n' % (i, coeff)
        ifstr = 'else if '

    num += "\n  return -1;"
    name += "  }\n  return NULL;"

    return (num, name)


def extract_coefficient_spaces(forms):
    """Extract a list of tuples

      (classname, finite_element_classname, dofmap_classname, coordinate_mapping_classname)

    for the coefficient spaces in the set of given forms. This can
    then be used for input to the function space template."""

    # Extract data for each coefficient space
    spaces = {}
    for form in forms:
        for (i, name) in enumerate(form.coefficient_names):
            # Skip if already considered
            if name in spaces:
                continue

            # Map element name, dof map name, etc to this coefficient
            assert len(form.ufc_coordinate_mapping_classnames) == 1
            spaces[name] = ("CoefficientSpace_{}".format(name),
                            form.ufc_finite_element_classnames[form.rank + i],
                            form.ufc_dofmap_classnames[form.rank + i],
                            form.ufc_coordinate_mapping_classnames[0])

    # Return coefficient spaces sorted alphabetically by coefficient name
    names = sorted(spaces.keys())
    return [spaces[name] for name in names]


def generate_function_space_typedefs(form, prefix, classname):
    """Generate typedefs for test, trial and coefficient spaces relative
    to a function space.

    """

    snippets = {"functionspace": ("TestSpace", "TrialSpace")}

    # Add convenience pointers to factory functions
    template0 = "static const dolfin_function_space_factory_ptr {0}{2}{1} = {0}{2}_FunctionSpace_{3};"
    factory0 = "\n".join(
        template0.format(prefix, snippets["functionspace"][i], classname, i)
        for i in range(form.rank))

    # FIXME: (GNW) These are function typedefs to functions typedefs,
    # and are giving trouble with a C compiler (fine with C++)
    template1 = "// static dolfin_function_space_factory_ptr {0}{2}CoefficientSpace_{1} = {0}{2}_FunctionSpace_{3};"
    factory1 = "\n".join(
        template1.format(prefix, form.coefficient_names[i], classname, form.rank + i)
        for i in range(form.num_coefficients))

    code = factory0 + "\n" + factory1
    return code


FORM_CLASS_TEMPLATE_DECL = """\
dolfin_form* {prefix}{classname}(void);

{typedefs}
"""

FORM_CLASS_TEMPLATE_IMPL = """\
// Return the number of the coefficient with this name. Returns -1 if name does not exist.
static int {prefix}{classname}_coefficient_number(const char* name)
{{
{coefficient_number}
}}

// Return the name of the coefficient with this number. Returns NULL if index is out-of-range.
static const char* {prefix}{classname}_coefficient_name(int i)
{{
{coefficient_name}
}}

dolfin_form* {prefix}{classname}()
{{
  dolfin_form* form = (dolfin_form*) malloc(sizeof(*form));
  form->form = create_{ufc_form};
  form->coefficient_name_map = {prefix}{classname}_coefficient_name;
  form->coefficient_number_map = {prefix}{classname}_coefficient_number;
  return form;
}}
"""

FUNCTION_SPACE_TEMPLATE_DECL = """\
dolfin_function_space* {prefix}{classname}(void);
"""

FUNCTION_SPACE_TEMPLATE_IMPL = """\
dolfin_function_space* {prefix}{classname}(void)
{{
  dolfin_function_space* space = (dolfin_function_space*) malloc(sizeof(*space));
  space->element = create_{finite_element_classname};
  space->dofmap = create_{dofmap_classname};
  space->coordinate_mapping = {coordinate_map_classname};
  return space;
}}
"""


class UFCFormNames:
    """Encapsulation of the names related to a generated UFC form."""

    def __init__(self, name, coefficient_names, ufc_form_classname, ufc_finite_element_classnames,
                 ufc_dofmap_classnames, ufc_coordinate_mapping_classnames):
        """Arguments:

        @param name:
            Name of form (e.g. 'a', 'L', 'M').
        @param coefficient_names:
            List of names of form coefficients (e.g. 'f', 'g').
        @param ufc_form_classname:
            Name of ufc::form subclass.
        @param ufc_finite_element_classnames:
            List of names of ufc::finite_element subclasses (length
            rank + num_coefficients).
        @param ufc_dofmap_classnames:
            List of names of ufc::dofmap subclasses (length rank +
            num_coefficients).
        @param ufc_coordinate_mapping_classnames:
            List of names of ufc::coordinate_mapping subclasses
        """
        assert len(coefficient_names) <= len(ufc_dofmap_classnames)
        assert len(ufc_finite_element_classnames) == len(ufc_dofmap_classnames)

        self.num_coefficients = len(coefficient_names)
        self.rank = len(ufc_finite_element_classnames) - self.num_coefficients
        self.name = name
        self.coefficient_names = coefficient_names
        self.ufc_form_classname = ufc_form_classname
        self.ufc_finite_element_classnames = ufc_finite_element_classnames
        self.ufc_dofmap_classnames = ufc_dofmap_classnames
        self.ufc_coordinate_mapping_classnames = ufc_coordinate_mapping_classnames


class UFCElementNames:
    """Encapsulation of the names related to a generated UFC element."""

    def __init__(self, name, element_classname, dofmap_classname, coordinate_mapping_classname):
        self.name = name
        self.element_classname = element_classname
        self.dofmap_classname = dofmap_classname
        self.coordinate_mapping_classname = coordinate_mapping_classname
