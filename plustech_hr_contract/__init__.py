# -*- coding: utf-8 -*-
#################################################################################
# Author      : Plus Tech.
# Copyright(c): 2021-Present TechPlus IT Solutions.
# All Rights Reserved.
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <www.plustech.com/license>
#################################################################################
import os
import sys
import subprocess
from odoo.exceptions import MissingError
from . import models


def pre_init_contract(cr):
    """
    This function installs required Packages or library
    """
    get_pckg = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'])
    installed_packages = [r.decode().split('==')[0] for r in get_pckg.split()]
    # List of your required packages
    required_packages = ['hijri_converter']
    try:
        for packg in required_packages:
            if packg in installed_packages:
                pass
            else:
                print('installing package %s' % packg)
                os.system('pip3 install ' + packg)
    except:
        raise MissingError('Package Hijri Converter could not installed but is required')
