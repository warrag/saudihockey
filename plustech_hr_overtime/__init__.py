from . import models
import os
import sys
import subprocess


def pre_init_hook(cr):
    """
    This function installs required Packages or library
    """
    get_pckg = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'])
    installed_packages = [r.decode().split('==')[0] for r in get_pckg.split()]
    # List of your required packages
    required_packages = ['pandas']
    try:
        for packg in required_packages:
            if packg in installed_packages:
                pass
            else:
                print('installing package %s' % packg)
                os.system('pip3 install ' + packg)
    except:
        pass
