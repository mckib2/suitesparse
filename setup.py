'''Build SuiteSparse.'''

import logging
import pathlib
import shutil
from typing import List, Tuple
logging.basicConfig()
logger = logging.getLogger('suitesparse-setup')
SS = pathlib.Path(__file__).parent / 'SuiteSparse'
tmp = pathlib.Path(__file__).parent / '.suitesparse_tmp'
DEBUG = True


def _add_macros(f: pathlib.Path, macros: List[str]):
    with open(f, 'r+') as fp:
        contents = fp.read()
        contents = '\n'.join(f'#define {macro}' for macro in macros if macro) + '\n' + contents
        fp.seek(0)
        fp.write(contents)
        fp.truncate()    


def _redirect_headers(f: pathlib.Path, headers: List[Tuple[str]]):
    with open(f, 'r+') as fp:
        contents = fp.read()
        for frum, to in headers:
            contents = contents.replace(f'#include "{frum}"', f'#include "{to}"')
        fp.seek(0)
        fp.write(contents)
        fp.truncate()    
            

def configuration(parent_package='', top_path=None):
    from numpy.distutils.misc_util import Configuration
    config = Configuration('suitesparse', parent_package, top_path)

    # SuiteSparse_config
    config.add_library(
        'suitesparseconfig',
        sources=[str(SS / 'SuiteSparse_config/SuiteSparse_config.c')],
        include_dirs=[str(SS / 'SuiteSparse_config')],
        depends=[str(SS / 'SuiteSparse_config/SuiteSparse_config.h')],
        language='c')

    # AMD
    shutil.copytree(SS / 'AMD/Source', tmp / 'AMDI/Source')
    shutil.copytree(SS / 'AMD/Source', tmp / 'AMDL/Source')
    for type_ in (('DINT', 'i', 'I'), ('DLONG', 'l', 'L')):
        for f in (tmp / f'AMD{type_[2]}/Source').glob('amd_*.c'):
            fnew = f.parent / f.name.replace('amd_', f'amd_{type_[1]}_')
            shutil.move(f, fnew)
            _add_macros(f=fnew, macros=[type_[0]])
    config.add_library(
        'amd',
        sources=[str(f) for f in (tmp / 'AMDI/Source').glob('amd_*.c')] + [str(f) for f in (tmp / 'AMDL/Source').glob('amd_*.c')],
        include_dirs=[str(SS / 'SuiteSparse_config'), str(SS / 'AMD/Include')],
        libraries=['suitesparseconfig'],
        language='c')

    # CAMD
    shutil.copytree(SS / 'CAMD/Source', tmp / 'CAMDI/Source')
    shutil.copytree(SS / 'CAMD/Source', tmp / 'CAMDL/Source')
    (tmp / 'CAMDI/Include').mkdir(exist_ok=True, parents=True)
    (tmp / 'CAMDL/Include').mkdir(exist_ok=True, parents=True)
    shutil.copyfile(SS / 'CAMD/Include/camd_internal.h', tmp / 'CAMDI/Include/camd_i_internal.h')
    shutil.copyfile(SS / 'CAMD/Include/camd_internal.h', tmp / 'CAMDL/Include/camd_l_internal.h')
    _add_macros(f=(tmp / f'CAMDI/Include/camd_i_internal.h'), macros=['DINT'])
    _add_macros(f=(tmp / f'CAMDL/Include/camd_l_internal.h'), macros=['DLONG'])
    for type_ in (('DINT', 'i', 'I'), ('DLONG', 'l', 'L')):
        for f in (tmp / f'CAMD{type_[2]}/Source').glob('camd_*.c'):
            fnew = f.parent / f.name.replace('camd_', f'camd_{type_[1]}_')
            shutil.move(f, fnew)
            _add_macros(f=fnew, macros=[type_[0]])
            _redirect_headers(f=fnew, headers=[('camd_internal.h', f'camd_{type_[1]}_internal.h')])
    config.add_library(
        'camd',
        sources=[str(f) for f in (tmp / 'CAMDI/Source').glob('camd_*.c')] + [str(f) for f in (tmp / 'CAMDL/Source').glob('camd_*.c')],
        include_dirs=[str(SS / 'SuiteSparse_config'), str(SS / 'CAMD/Include'), str(tmp / 'CAMDI/Include'), str(tmp / 'CAMDL/Include')],
        libraries=['suitesparseconfig'],
        language='c')

    # COLAMD
    shutil.copytree(SS / 'COLAMD/Source', tmp / 'COLAMDI/Source')
    shutil.copytree(SS / 'COLAMD/Source', tmp / 'COLAMDL/Source')
    for type_ in (('', '', 'I'), ('DLONG', '_l', 'L')):
        f = (tmp / f'COLAMD{type_[2]}/Source/colamd.c')
        fnew = f.parent / f'colamd{type_[1]}.c'
        shutil.move(f, fnew)
        _add_macros(f=fnew, macros=[type_[0]])
    config.add_library(
        'colamd',
        sources=[str(tmp / 'COLAMDI/Source/colamd.c'), str(tmp / 'COLAMDL/Source/colamd_l.c')],
        include_dirs=[str(SS / 'SuiteSparse_config'), str(SS / 'COLAMD/Include')],
        libraries=['suitesparseconfig'],
        language='c')

    # CCOLAMD
    shutil.copytree(SS / 'CCOLAMD/Source', tmp / 'CCOLAMDI/Source')
    shutil.copytree(SS / 'CCOLAMD/Source', tmp / 'CCOLAMDL/Source')
    for type_ in (('', '', 'I'), ('DLONG', '_l', 'L')):
        f = (tmp / f'CCOLAMD{type_[2]}/Source/ccolamd.c')
        fnew = f.parent / f'ccolamd{type_[1]}.c'
        shutil.move(f, fnew)
        _add_macros(f=fnew, macros=[type_[0]])
    config.add_library(
        'ccolamd',
        sources=[str(tmp / 'CCOLAMDI/Source/ccolamd.c'), str(tmp / 'CCOLAMDL/Source/ccolamd_l.c')],
        include_dirs=[str(SS / 'SuiteSparse_config'), str(SS / 'CCOLAMD/Include')],
        libraries=['suitesparseconfig'],
        language='c')

    # CHOLMOD/Check module
    cholmod_sources = [str(SS / 'CHOLMOD/Check/cholmod_check.c'),
                       str(SS / 'CHOLMOD/Check/cholmod_read.c'),
                       str(SS / 'CHOLMOD/Check/cholmod_write.c'),
                       str(tmp / 'CHOLMODL/Check/cholmod_l_check.c'),
                       str(tmp / 'CHOLMODL/Check/cholmod_l_read.c'),
                       str(tmp / 'CHOLMODL/Check/cholmod_l_write.c')]
    cholmod_includes = [str(SS / 'AMD/Include'),
                        str(SS / 'AMD/Source'),
                        str(SS / 'COLAMD/Include'),
                        str(SS / 'CHOLMOD/Include'),
                        str(tmp / 'CHOLMODL/Include')]
    shutil.copytree(SS / 'CHOLMOD/Check', tmp / 'CHOLMODL/Check')
    shutil.copytree(SS / 'CHOLMOD/Include', tmp / 'CHOLMODL/Include')
    cholmod_l_hdrs = [(hdr.name, hdr.name.replace('cholmod', 'cholmod_l')) for hdr in (SS / 'CHOLMOD/Include').glob('*.h')]
    for f in (tmp / 'CHOLMODL/Include').glob('*.h'):
        fnew = f.parent / f.name.replace('cholmod', 'cholmod_l')
        shutil.move(f, fnew)
        _add_macros(f=fnew, macros=['DLONG'])
        _redirect_headers(f=fnew, headers=cholmod_l_hdrs)

    for f in (tmp / 'CHOLMODL/Check').glob('cholmod_*.c'):
        fnew = f.parent / f.name.replace('cholmod_', 'cholmod_l_')
        shutil.move(f, fnew)
        _add_macros(f=fnew, macros=['DLONG'])
        _redirect_headers(f=fnew, headers=[('cholmod_internal.h', 'cholmod_l_internal.h'),
                                           ('cholmod_check.h', 'cholmod_l_check.h'),
                                           ('cholmod_config.h', 'cholmod_l_config.h'),
                                           ('cholmod_matrixops.h', 'cholmod_l_matrixops.h')])

    # CHOLMOD/Core module
    cholmod_sources += [str(SS / 'CHOLMOD/Core/cholmod_common.c'),
                        str(SS / 'CHOLMOD/Core/cholmod_change_factor.c'),
                        str(SS / 'CHOLMOD/Core/cholmod_memory.c'),
                        str(SS / 'CHOLMOD/Core/cholmod_sparse.c'),
                        str(SS / 'CHOLMOD/Core/cholmod_complex.c'),
                        str(SS / 'CHOLMOD/Core/cholmod_band.c'),
                        str(SS / 'CHOLMOD/Core/cholmod_copy.c'),
                        str(SS / 'CHOLMOD/Core/cholmod_error.c'),
                        str(SS / 'CHOLMOD/Core/cholmod_aat.c'),
                        str(SS / 'CHOLMOD/Core/cholmod_add.c'),
                        str(SS / 'CHOLMOD/Core/cholmod_version.c'),
                        
                        str(tmp / 'CHOLMODL/Core/cholmod_l_common.c'),
                        str(tmp / 'CHOLMODL/Core/cholmod_l_change_factor.c'),
                        str(tmp / 'CHOLMODL/Core/cholmod_l_memory.c'),
                        str(tmp / 'CHOLMODL/Core/cholmod_l_sparse.c'),
                        str(tmp / 'CHOLMODL/Core/cholmod_l_complex.c'),
                        str(tmp / 'CHOLMODL/Core/cholmod_l_band.c'),
                        str(tmp / 'CHOLMODL/Core/cholmod_l_copy.c'),
                        str(tmp / 'CHOLMODL/Core/cholmod_l_error.c'),
                        str(tmp / 'CHOLMODL/Core/cholmod_l_aat.c'),
                        str(tmp / 'CHOLMODL/Core/cholmod_l_add.c'),
                        str(tmp / 'CHOLMODL/Core/cholmod_l_version.c')]
    shutil.copytree(SS / 'CHOLMOD/Core', tmp / 'CHOLMODL/Core')
    for f in (tmp / 'CHOLMODL/Core').glob('*.c'):
        fnew = f.parent / f.name.replace('cholmod_', 'cholmod_l_')
        shutil.move(f, fnew)
        _add_macros(f=fnew, macros=['DLONG'])
        _redirect_headers(f=fnew, headers=cholmod_l_hdrs + [('t_cholmod_change_factor.c', 't_cholmod_l_change_factor.c'),
                                                            ('t_cholmod_dense', 't_cholmod_l_dense'),
                                                            ('t_cholmod_transpose', 't_cholmod_l_transpose'),
                                                            ('t_cholmod_triplet', 't_cholmod_l_triplet')])

    # CHOLMOD/Cholesky module
    cholmod_sources += [str(f) for f in (SS / 'CHOLMOD/Cholesky').glob('cholmod_*.c')]
    cholmod_sources += [str(f) for f in (tmp / 'CHOLMODL/Cholesky').glob('cholmod_*.c')]    
    shutil.copytree(SS / 'CHOLMOD/Cholesky', tmp / 'CHOLMODL/Cholesky')
    for f in (tmp / 'CHOLMODL/Cholesky').glob('*.c'):
        fnew = f.parent / f.name.replace('cholmod_', 'cholmod_l_')
        shutil.move(f, fnew)
        _add_macros(f=fnew, macros=['DLONG'])
        _redirect_headers(f=fnew, headers=cholmod_l_hdrs + [('t_cholmod_lsolve.c', 't_cholmod_l_lsolve.c'),
                                                            ('t_cholmod_ltsolve.c', 't_cholmod_l_ltsolve.c'),
                                                            ('t_cholmod_rowfac.c', 't_cholmod_l_rowfac.c'),
                                                            ('t_cholmod_solve.c', 't_cholmod_l_solve.c')])
    
    # CHOLMOD/Partition module
    cholmod_includes += [str(SS / 'metis-5.1.0/include'), str(SS / 'CAMD/Include'), str(SS / 'CCOLAMD/Include')]
    cholmod_sources += [str(f) for f in (SS / 'CHOLMOD/Partition').glob('cholmod_*.c')]
    cholmod_sources += [str(f) for f in (tmp / 'CHOLMODL/Partition').glob('cholmod_l_*.c')]    
    shutil.copytree(SS / 'CHOLMOD/Partition', tmp / 'CHOLMODL/Parititon')
    for f in (tmp / 'CHOLMODL/Parititon').glob('*.c'):
        fnew = f.parent / f.name.replace('cholmod_', 'cholmod_l_')
        shutil.move(f, fnew)
        _add_macros(f=fnew, macros=['DLONG'])
        _redirect_headers(f=fnew, headers=cholmod_l_hdrs)

    # CHOLMOD/MatrixOps module
    cholmod_sources += [str(f) for f in (SS / 'CHOLMOD/MatrixOps').glob('cholmod_*.c')]
    cholmod_sources += [str(f) for f in (tmp / 'CHOLMODL/MatrixOps').glob('cholmod_l_*.c')]    
    shutil.copytree(SS / 'CHOLMOD/MatrixOps', tmp / 'CHOLMODL/MatrixOps')
    for f in (tmp / 'CHOLMODL/MatrixOps').glob('*.c'):
        fnew = f.parent / f.name.replace('cholmod_', 'cholmod_l_')
        shutil.move(f, fnew)
        _add_macros(f=fnew, macros=['DLONG'])
        _redirect_headers(f=fnew, headers=cholmod_l_hdrs + [('t_cholmod_sdmult.c', 't_cholmod_l_sdmult.c')])

    # CHOLMOD/Modify module
    cholmod_sources += [str(f) for f in (SS / 'CHOLMOD/Modify').glob('cholmod_*.c')]
    cholmod_sources += [str(f) for f in (tmp / 'CHOLMODL/Modify').glob('cholmod_l_*.c')]    
    shutil.copytree(SS / 'CHOLMOD/Modify', tmp / 'CHOLMODL/Modify')
    for f in (tmp / 'CHOLMODL/Modify').glob('*.c'):
        fnew = f.parent / f.name.replace('cholmod_', 'cholmod_l_')
        shutil.move(f, fnew)
        _add_macros(f=fnew, macros=['DLONG'])
        _redirect_headers(f=fnew, headers=cholmod_l_hdrs + [('t_cholmod_updown.c', 't_cholmod_l_updown.c'),
                                                            ('t_cholmod_updown_numkr.c', 't_cholmod_l_updown_numkr.c')])

    # CHOLMOD/Supernodal module
    cholmod_sources += [str(f) for f in (SS / 'CHOLMOD/Supernodal').glob('cholmod_*.c')]
    cholmod_sources += [str(f) for f in (tmp / 'CHOLMODL/Supernodal').glob('cholmod_l_*.c')]    
    shutil.copytree(SS / 'CHOLMOD/Supernodal', tmp / 'CHOLMODL/Supernodal')
    for f in (tmp / 'CHOLMODL/Supernodal').glob('*.c'):
        fnew = f.parent / f.name.replace('cholmod_', 'cholmod_l_')
        shutil.move(f, fnew)
        _add_macros(f=fnew, macros=['DLONG'])
        _redirect_headers(f=fnew, headers=cholmod_l_hdrs + [('t_cholmod_super_numeric.c', 't_cholmod_l_super_numeric.c'),
                                                            ('t_cholmod_super_solve.c', 't_cholmod_l_super_solve.c')])

    # CHOLMOD
    config.add_library(
        'cholmod',
        sources=cholmod_sources,
        include_dirs=[str(SS / 'SuiteSparse_config')] + cholmod_includes,
        libraries=['amd', 'colamd', 'suitesparseconfig', 'lapack', 'blas'],
        language='c')    
    
    return config


if __name__ == '__main__':
    from numpy.distutils.core import setup

    # Turn on logging of we're in DEBUG mode
    if DEBUG:
        logger.setLevel(logging.INFO)

    # try...finally statement ensures tmp dir is removed at end
    # of setup
    try:
        if tmp.exists():
            logger.info(f'Removing tmp dir {tmp} to start')
            shutil.rmtree(tmp)
        tmp.mkdir()
        setup(**configuration().todict())
    finally:
        if DEBUG:
            logger.info(f'Not removing tmp dir {tmp}')
        else:
            shutil.rmtree(tmp)
