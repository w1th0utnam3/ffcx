# -*- coding: utf-8 -*-
# Copyright (C) 2011-2017 Martin Sandve Alnæs
#
# This file is part of FFC (https://www.fenicsproject.org)
#
# SPDX-License-Identifier:    LGPL-3.0-or-later
"""Collection of FFC specific pieces for the code generation phase."""

import ffc.uflacs.language.cnodes
from ffc.uflacs.language.ufl_to_cnodes import UFL2CNodesTranslatorCpp
from ffc.backends.ffc.symbols import FFCBackendSymbols
from ffc.backends.ffc.access import FFCBackendAccess
from ffc.backends.ffc.definitions import FFCBackendDefinitions


class FFCBackend(object):
    """Class collecting all aspects of the FFC backend."""

    def __init__(self, ir, parameters):

        # This is the seam where cnodes/C is chosen for the ffc backend
        self.language = ffc.uflacs.language.cnodes
        self.ufl_to_language = UFL2CNodesTranslatorCpp(self.language)

        coefficient_numbering = ir["coefficient_numbering"]
        self.symbols = FFCBackendSymbols(self.language, coefficient_numbering)
        self.definitions = FFCBackendDefinitions(ir, self.language,
                                                 self.symbols, parameters)
        self.access = FFCBackendAccess(ir, self.language, self.symbols,
                                       parameters)
