'''Build SuiteSparse.'''

import logging
import pathlib
import shutil
from typing import List, Tuple
import re
logging.basicConfig()
logger = logging.getLogger('suitesparse-setup')
SS = pathlib.Path(__file__).parent / 'SuiteSparse'
tmp = pathlib.Path(__file__).parent / '.sstmp'
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
    from numpy.distutils.system_info import get_info
    config = Configuration('suitesparse', parent_package, top_path)

    # SuiteSparse_config
    ss_config_opts = {
        'name': 'suitesparseconfig',
        'sources': [str((SS / 'SuiteSparse_config/SuiteSparse_config.c').relative_to(SS.parent))],
        'include_dirs': [str((SS / 'SuiteSparse_config').relative_to(SS.parent))],
        'language': 'c',
    }
    config.add_library(**ss_config_opts)
    config.add_extension(**ss_config_opts,
                         extra_info={
                             'sources': ['suitesparseconfig_impl.c'],
                             'libraries': ['suitesparseconfig'],
                         })
    
    # AMD
    if not (tmp / 'AMDI/Include').exists():
        (tmp / 'AMDI/Include').mkdir(exist_ok=True, parents=True)
        (tmp / 'AMDL/Include').mkdir(exist_ok=True, parents=True)
        shutil.copyfile(SS / 'AMD/Include/amd_internal.h', tmp / 'AMDI/Include/amd_i_internal.h')
        shutil.copyfile(SS / 'AMD/Include/amd_internal.h', tmp / 'AMDL/Include/amd_l_internal.h')
        _add_macros(f=(tmp / 'AMDI/Include/amd_i_internal.h'), macros=['DINT'])
        _add_macros(f=(tmp / 'AMDL/Include/amd_l_internal.h'), macros=['DLONG'])
    if not (tmp / 'AMDI/Source').exists():
        shutil.copytree(SS / 'AMD/Source', tmp / 'AMDI/Source')
        shutil.copytree(SS / 'AMD/Source', tmp / 'AMDL/Source')
        for type_ in (('DINT', 'i', 'I'),
                      ('DLONG', 'l', 'L')):
            for f in (tmp / f'AMD{type_[2]}/Source').glob('amd_*.c'):
                fnew = f.parent / f.name.replace('amd_', f'amd_{type_[1]}_')
                shutil.move(f, fnew)
                _add_macros(f=fnew, macros=[type_[0]])
                _redirect_headers(f=fnew, headers=[('amd_internal.h', f'amd_{type_[1]}_internal.h')])

    amd_opts = {
        'name': 'amd',
        'sources': ([str(f.relative_to(SS.parent))
                     for f in (tmp / 'AMDI/Source').glob('amd_*.c')] +
                    [str(f.relative_to(SS.parent))
                     for f in (tmp / 'AMDL/Source').glob('amd_*.c')]),
        'include_dirs': [
            str((SS / 'SuiteSparse_config').relative_to(SS.parent)),
            str((SS / 'AMD/Include').relative_to(SS.parent)),
            str((tmp / 'AMDI/Include').relative_to(SS.parent)),
            str((tmp / 'AMDL/Include').relative_to(SS.parent)),
        ],
        'libraries': ['suitesparseconfig'],
        'language': 'c',
    }
    config.add_library(**amd_opts)
    config.add_extension(**amd_opts, extra_info={
        'sources': ['amd_impl.c'],
        'export_symbols':[
            'amd_order', 'amd_l_order', 'amd_2', 'amd_l2', 'amd_valid',
            'amd_l_valid', 'amd_defaults', 'amd_l_defaults', 'amd_control',
            'amd_l_control', 'amd_info', 'amd_l_info',
        ],
        'libraries': ['amd'],
    })

    # CAMD
    if not (tmp / 'CAMDI/Include').exists():
        (tmp / 'CAMDI/Include').mkdir(exist_ok=True, parents=True)
        (tmp / 'CAMDL/Include').mkdir(exist_ok=True, parents=True)
        shutil.copyfile(SS / 'CAMD/Include/camd_internal.h', tmp / 'CAMDI/Include/camd_i_internal.h')
        shutil.copyfile(SS / 'CAMD/Include/camd_internal.h', tmp / 'CAMDL/Include/camd_l_internal.h')
        _add_macros(f=(tmp / f'CAMDI/Include/camd_i_internal.h'), macros=['DINT'])
        _add_macros(f=(tmp / f'CAMDL/Include/camd_l_internal.h'), macros=['DLONG'])
    if not (tmp / 'CAMDI/Source').exists():
        shutil.copytree(SS / 'CAMD/Source', tmp / 'CAMDI/Source')
        shutil.copytree(SS / 'CAMD/Source', tmp / 'CAMDL/Source')
        for type_ in (('DINT', 'i', 'I'), ('DLONG', 'l', 'L')):
            for f in (tmp / f'CAMD{type_[2]}/Source').glob('camd_*.c'):
                fnew = f.parent / f.name.replace('camd_', f'camd_{type_[1]}_')
                shutil.move(f, fnew)
                _add_macros(f=fnew, macros=[type_[0]])
                _redirect_headers(f=fnew, headers=[('camd_internal.h', f'camd_{type_[1]}_internal.h')])

    camd_opts = {
        'name': 'camd',
        'sources': ([str(f.relative_to(SS.parent))
                     for f in (tmp / 'CAMDI/Source').glob('camd_*.c')] +
                    [str(f.relative_to(SS.parent))
                     for f in (tmp / 'CAMDL/Source').glob('camd_*.c')]),
        'include_dirs': [
            str((SS / 'SuiteSparse_config').relative_to(SS.parent)),
            str((SS / 'CAMD/Include').relative_to(SS.parent)),
            str((tmp / 'CAMDI/Include').relative_to(SS.parent)),
            str((tmp / 'CAMDL/Include').relative_to(SS.parent)),
        ],
        'libraries': ['suitesparseconfig'],
        'language': 'c',
    }
                
    config.add_library(**camd_opts)
    config.add_extension(**camd_opts, extra_info={
        'sources': ['camd_impl.c'],
        'export_symbols': [
            'camd_order', 'camd_l_order', 'camd_2', 'camd_l2', 'camd_valid',
            'camd_l_valid', 'camd_cvalid', 'camd_l_cvalid', 'camd_defaults',
            'camd_l_defaults', 'camd_control', 'camd_l_control', 'camd_info',
            'camd_l_info',
        ],
        'libraries': ['camd'],
    })

    # COLAMD
    if not (tmp / 'COLAMDI/Source').exists():
        shutil.copytree(SS / 'COLAMD/Source', tmp / 'COLAMDI/Source')
        shutil.copytree(SS / 'COLAMD/Source', tmp / 'COLAMDL/Source')
        for type_ in (('', '', 'I'), ('DLONG', '_l', 'L')):
            f = (tmp / f'COLAMD{type_[2]}/Source/colamd.c')
            fnew = f.parent / f'colamd{type_[1]}.c'
            shutil.move(f, fnew)
            _add_macros(f=fnew, macros=[type_[0]])

    colamd_opts = {
        'name': 'colamd',
        'sources': [
            str((tmp / 'COLAMDI/Source/colamd.c').relative_to(SS.parent)),
            str((tmp / 'COLAMDL/Source/colamd_l.c').relative_to(SS.parent)),
        ],
        'include_dirs': [
            str((SS / 'SuiteSparse_config').relative_to(SS.parent)),
            str((SS / 'COLAMD/Include').relative_to(SS.parent)),
        ],
        'libraries': ['suitesparseconfig'],
        'language': 'c',
    }
            
    config.add_library(**colamd_opts)
    config.add_extension(**colamd_opts, extra_info={
        'sources': ['colamd_impl.c'],
        'libraries': ['colamd'],
        'export_symbols': [
            'colamd_recommended', 'colamd_l_recommended',
            'colamd_set_defaults', 'colamd_l_set_defaults',
            'colamd', 'colamd_l', 'symamd', 'symamd_l',
            'colamd_report', 'colamd_l_report',
            'symamd_report', 'symamd_l_report',
        ],
    })

    # CCOLAMD
    if not (tmp / 'CCOLAMDI/Source').exists():
        shutil.copytree(SS / 'CCOLAMD/Source', tmp / 'CCOLAMDI/Source')
        shutil.copytree(SS / 'CCOLAMD/Source', tmp / 'CCOLAMDL/Source')
        for type_ in (('', '', 'I'), ('DLONG', '_l', 'L')):
            f = (tmp / f'CCOLAMD{type_[2]}/Source/ccolamd.c')
            fnew = f.parent / f'ccolamd{type_[1]}.c'
            shutil.move(f, fnew)
            _add_macros(f=fnew, macros=[type_[0]])

    ccolamd_opts = {
        'name': 'ccolamd',
        'sources': [
            str((tmp / 'CCOLAMDI/Source/ccolamd.c').relative_to(SS.parent)),
            str((tmp / 'CCOLAMDL/Source/ccolamd_l.c').relative_to(SS.parent)),
        ],
        'include_dirs': [
            str((SS / 'SuiteSparse_config').relative_to(SS.parent)),
            str((SS / 'CCOLAMD/Include').relative_to(SS.parent)),
        ],
        'libraries': ['suitesparseconfig'],
        'language': 'c',
    }
            
    config.add_library(**ccolamd_opts)
    config.add_extension(**ccolamd_opts, extra_info={
        'sources': ['ccolamd_impl.c'],
        'libraries': ['ccolamd'],
        'export_symbols': [
            'ccolamd_recommended', 'ccolamd_l_recommended',
            'ccolamd_set_defaults', 'ccolamd_l_set_defaults',
            'ccolamd', 'ccolamd_l', 'csymamd', 'csymamd_l',
            'ccolamd_report', 'ccolamd_l_report',
            'csymamd_report', 'csymamd_l_report',
            'ccolamd2', 'ccolamd2_l',
            'ccolamd_apply_order', 'ccolamd_l_apply_order',
            'ccolamd_fsize', 'ccolamd_l_fsize',
            'ccolamd_postorder', 'ccolamd_l_postorder',
            'ccolamd_post_tree', 'ccolamd_l_post_tree',
        ],
    })

    # CHOLMOD/Check module
    cholmod_sources = [str((SS / 'CHOLMOD/Check/cholmod_check.c').relative_to(SS.parent)),
                       str((SS / 'CHOLMOD/Check/cholmod_read.c').relative_to(SS.parent)),
                       str((SS / 'CHOLMOD/Check/cholmod_write.c').relative_to(SS.parent)),
                       str((tmp / 'CHOLMODL/Check/cholmod_l_check.c').relative_to(SS.parent)),
                       str((tmp / 'CHOLMODL/Check/cholmod_l_read.c').relative_to(SS.parent)),
                       str((tmp / 'CHOLMODL/Check/cholmod_l_write.c').relative_to(SS.parent))]
    cholmod_includes = [str((SS / 'AMD/Include').relative_to(SS.parent)),
                        str((SS / 'AMD/Source').relative_to(SS.parent)),
                        str((SS / 'COLAMD/Include').relative_to(SS.parent)),
                        str((SS / 'CHOLMOD/Include').relative_to(SS.parent)),
                        str((tmp / 'CHOLMODL/Include').relative_to(SS.parent))]

    cholmod_l_hdrs = [(hdr.name, hdr.name.replace('cholmod', 'cholmod_l')) for hdr in (SS / 'CHOLMOD/Include').glob('*.h')]
    if not (tmp / 'CHOLMODL/Include').exists():
        shutil.copytree(SS / 'CHOLMOD/Include', tmp / 'CHOLMODL/Include')
        for f in (tmp / 'CHOLMODL/Include').glob('*.h'):
            fnew = f.parent / f.name.replace('cholmod', 'cholmod_l')
            shutil.move(f, fnew)
            _add_macros(f=fnew, macros=['DLONG'])
            _redirect_headers(f=fnew, headers=cholmod_l_hdrs)

    if not (tmp / 'CHOLMODL/Check').exists():
        shutil.copytree(SS / 'CHOLMOD/Check', tmp / 'CHOLMODL/Check')
        for f in (tmp / 'CHOLMODL/Check').glob('cholmod_*.c'):
            fnew = f.parent / f.name.replace('cholmod_', 'cholmod_l_')
            shutil.move(f, fnew)
            _add_macros(f=fnew, macros=['DLONG'])
            _redirect_headers(f=fnew, headers=[('cholmod_internal.h', 'cholmod_l_internal.h'),
                                               ('cholmod_check.h', 'cholmod_l_check.h'),
                                               ('cholmod_config.h', 'cholmod_l_config.h'),
                                               ('cholmod_matrixops.h', 'cholmod_l_matrixops.h')])

    # CHOLMOD/Core module
    cholmod_sources += [str(f.relative_to(SS.parent)) for f in (SS / 'CHOLMOD/Core').glob('cholmod_*.c')]
    cholmod_sources += [str(f.relative_to(SS.parent)) for f in (tmp / 'CHOLMODL/Core').glob('cholmod_*.c')]
    if not (tmp / 'CHOLMODL/Core').exists():
        shutil.copytree(SS / 'CHOLMOD/Core', tmp / 'CHOLMODL/Core')
        for f in (tmp / 'CHOLMODL/Core').glob('*.c'):
            fnew = f.parent / f.name.replace('cholmod_', 'cholmod_l_')
            shutil.move(f, fnew)
            _add_macros(f=fnew, macros=['DLONG'])
            _redirect_headers(f=fnew, headers=cholmod_l_hdrs + [('t_cholmod_change_factor.c', 't_cholmod_l_change_factor.c'),
                                                                ('t_cholmod_dense.c', 't_cholmod_l_dense.c'),
                                                                ('t_cholmod_transpose.c', 't_cholmod_l_transpose.c'),
                                                                ('t_cholmod_triplet.c', 't_cholmod_l_triplet.c')])

    # CHOLMOD/Cholesky module
    cholmod_sources += [str(f.relative_to(SS.parent)) for f in (SS / 'CHOLMOD/Cholesky').glob('cholmod_*.c')]
    cholmod_sources += [str(f.relative_to(SS.parent)) for f in (tmp / 'CHOLMODL/Cholesky').glob('cholmod_*.c')]
    if not (tmp / 'CHOLMODL/Cholesky').exists():
        shutil.copytree(SS / 'CHOLMOD/Cholesky', tmp / 'CHOLMODL/Cholesky')
        for f in (tmp / 'CHOLMODL/Cholesky').glob('*.c'):
            fnew = f.parent / f.name.replace('cholmod_', 'cholmod_l_')
            shutil.move(f, fnew)
            _add_macros(f=fnew, macros=['DLONG'])
            _redirect_headers(f=fnew, headers=cholmod_l_hdrs + [('t_cholmod_lsolve.c', 't_cholmod_l_lsolve.c'),
                                                                ('t_cholmod_ltsolve.c', 't_cholmod_l_ltsolve.c'),
                                                                ('t_cholmod_rowfac.c', 't_cholmod_l_rowfac.c'),
                                                                ('t_cholmod_solve.c', 't_cholmod_l_solve.c'),
                                                                ('t_cholmod_dense.c', 't_cholmod_l_dense.c')])
    
    # CHOLMOD/Partition module
    cholmod_includes += [
        str((SS / 'metis-5.1.0/include').relative_to(SS.parent)),
        str((SS / 'CAMD/Include').relative_to(SS.parent)),
        str((SS / 'CCOLAMD/Include').relative_to(SS.parent)),
    ]
    cholmod_sources += [str(f.relative_to(SS.parent)) for f in (SS / 'CHOLMOD/Partition').glob('cholmod_*.c')]
    cholmod_sources += [str(f.relative_to(SS.parent)) for f in (tmp / 'CHOLMODL/Partition').glob('cholmod_l_*.c')]
    if not (tmp / 'CHOLMODL/Parititon').exists():
        shutil.copytree(SS / 'CHOLMOD/Partition', tmp / 'CHOLMODL/Parititon')
        for f in (tmp / 'CHOLMODL/Parititon').glob('*.c'):
            fnew = f.parent / f.name.replace('cholmod_', 'cholmod_l_')
            shutil.move(f, fnew)
            _add_macros(f=fnew, macros=['DLONG'])
            _redirect_headers(f=fnew, headers=cholmod_l_hdrs)

    # CHOLMOD/MatrixOps module
    cholmod_sources += [str(f.relative_to(SS.parent)) for f in (SS / 'CHOLMOD/MatrixOps').glob('cholmod_*.c')]
    cholmod_sources += [str(f.relative_to(SS.parent)) for f in (tmp / 'CHOLMODL/MatrixOps').glob('cholmod_l_*.c')]
    if not (tmp / 'CHOLMODL/MatrixOps').exists():
        shutil.copytree(SS / 'CHOLMOD/MatrixOps', tmp / 'CHOLMODL/MatrixOps')
        for f in (tmp / 'CHOLMODL/MatrixOps').glob('*.c'):
            fnew = f.parent / f.name.replace('cholmod_', 'cholmod_l_')
            shutil.move(f, fnew)
            _add_macros(f=fnew, macros=['DLONG'])
            _redirect_headers(f=fnew, headers=cholmod_l_hdrs + [('t_cholmod_sdmult.c', 't_cholmod_l_sdmult.c')])

    # CHOLMOD/Modify module
    cholmod_sources += [str(f.relative_to(SS.parent)) for f in (SS / 'CHOLMOD/Modify').glob('cholmod_*.c')]
    cholmod_sources += [str(f.relative_to(SS.parent)) for f in (tmp / 'CHOLMODL/Modify').glob('cholmod_l_*.c')]
    if not (tmp / 'CHOLMODL/Modify').exists():
        shutil.copytree(SS / 'CHOLMOD/Modify', tmp / 'CHOLMODL/Modify')
        for f in (tmp / 'CHOLMODL/Modify').glob('*.c'):
            fnew = f.parent / f.name.replace('cholmod_', 'cholmod_l_')
            shutil.move(f, fnew)
            _add_macros(f=fnew, macros=['DLONG'])
            _redirect_headers(f=fnew, headers=cholmod_l_hdrs + [('t_cholmod_updown.c', 't_cholmod_l_updown.c'),
                                                                ('t_cholmod_updown_numkr.c', 't_cholmod_l_updown_numkr.c')])

    # CHOLMOD/Supernodal module
    cholmod_sources += [str(f.relative_to(SS.parent)) for f in (SS / 'CHOLMOD/Supernodal').glob('cholmod_*.c')]
    cholmod_sources += [str(f.relative_to(SS.parent)) for f in (tmp / 'CHOLMODL/Supernodal').glob('cholmod_l_*.c')]
    if not (tmp / 'CHOLMODL/Supernodal').exists():
        shutil.copytree(SS / 'CHOLMOD/Supernodal', tmp / 'CHOLMODL/Supernodal')
        for f in (tmp / 'CHOLMODL/Supernodal').glob('*.c'):
            fnew = f.parent / f.name.replace('cholmod_', 'cholmod_l_')
            shutil.move(f, fnew)
            _add_macros(f=fnew, macros=['DLONG'])
            _redirect_headers(f=fnew, headers=cholmod_l_hdrs + [('t_cholmod_super_numeric.c', 't_cholmod_l_super_numeric.c'),
                                                                ('t_cholmod_super_solve.c', 't_cholmod_l_super_solve.c')])

    # CHOLMOD
    #lapack_info = get_info('lapack')
    cholmod_opts = {
        'name': 'cholmod',
        'sources': cholmod_sources,
        'include_dirs': [str((SS / 'SuiteSparse_config').relative_to(SS.parent))] + cholmod_includes,
        'libraries': ['amd', 'colamd', 'suitesparseconfig'],
        'language': 'c',
    }
    config.add_library(**cholmod_opts, macros=[('NPARTITION', None)])
    config.add_extension(**cholmod_opts, extra_info={
        'sources': ['cholmod_impl.c'],
        'libraries': ['cholmod', 'openblas'],
        'define_macros': [('NPARTITION', None)],
        'export_symbols': [],
    })

    return config
    
    # SPQR
    config.add_library(
        'spqr',
        sources=[str(f.relative_to(SS.parent)) for f in (SS / 'SPQR/Source').glob('*.cpp')],
        include_dirs=[
            str((SS / 'SPQR/Include').relative_to(SS.parent)),
            str((SS / 'CHOLMOD/Include').relative_to(SS.parent)),
            str((SS / 'SuiteSparse_config').relative_to(SS.parent)),
        ],
        libraries=['amd', 'colamd', 'cholmod', 'suitesparseconfig'],
        language='c')

    shutil.copytree(SS / 'UMFPACK/Source', tmp / 'UMFPACKI/Source')
    shutil.copytree(SS / 'UMFPACK/Source', tmp / 'UMFPACKL/Source')
    shutil.copytree(SS / 'UMFPACK/Source', tmp / 'UMFPACKDI/Source')
    shutil.copytree(SS / 'UMFPACK/Source', tmp / 'UMFPACKDL/Source')
    shutil.copytree(SS / 'UMFPACK/Source', tmp / 'UMFPACKZI/Source')
    shutil.copytree(SS / 'UMFPACK/Source', tmp / 'UMFPACKZL/Source')
    umf_hdrs = {}
    for type_, macros in [('i', ['DINT']),
                          ('l', ['DLONG']),
                          ('di', ['DINT']),
                          ('dl', ['DLONG']),
                          ('zi', ['ZINT']),
                          ('zl', ['ZLONG'])]:
        umf_hdrs[type_] = ([(f.name, f.name.replace('umf_', f'umf_{type_}_'))
                            for f in (SS / 'UMFPACK/Source').glob('umf_*.h')] +
                           [(f.name, f.name.replace('umfpack_', f'umfpack_{type_}_'))
                            for f in (SS / 'UMFPACK/Source').glob('umfpack_*.h')] +
                           [('amd_internal.h', f'amd_{type_[-1] if type_ != "zl" else type_}_internal.h')])
        for f in (tmp / f'UMFPACK{type_.upper()}/Source/').glob('umf_*.h'):
            fnew = f.parent / f.name.replace('umf_', f'umf_{type_}_')
            shutil.move(f, fnew.relative_to(SS.parent))
            _add_macros(f=fnew, macros=macros)
            _redirect_headers(f=fnew, headers=umf_hdrs[type_])

    # non-user-callable umf_*.[ch] files, int/SuiteSparse_long versions only
    # (no real/complex):
    UMFINT = ['umf_analyze', 'umf_apply_order', 'umf_colamd', 'umf_free',
              'umf_fsize', 'umf_is_permutation', 'umf_malloc', 'umf_realloc',
              'umf_report_perm', 'umf_singletons', 'umf_cholmod']
    umfpack_sources = []
    for type_, macro in [('i', 'DINT'), ('l', 'DLONG')]:
        for f0 in UMFINT:
            f = tmp / f'UMFPACK{type_.upper()}/Source/{f0}.c'
            fnew = f.parent / f.name.replace('umf_', f'umf_{type_}_')
            umfpack_sources.append(str(fnew.relative_to(SS.parent)))
            shutil.move(f, fnew)
            _add_macros(f=fnew, macros=[macro])
            _redirect_headers(f=fnew, headers=umf_hdrs[type_])
        
    # non-user-callable, created from umf_ltsolve.c, umf_utsolve.c,
    # umf_triplet.c, and umf_assemble.c , with int/SuiteSparse_long
    # and real/complex versions:
    UMF_CREATED = ['umf_lhsolve', 'umf_uhsolve', 'umf_triplet_map_nox',
                   'umf_triplet_nomap_x', 'umf_triplet_nomap_nox',
                   'umf_triplet_map_x', 'umf_assemble_fixq',
                   'umf_store_lu_drop']

    # non-user-callable umf_*.[ch] files:
    UMFCH = ['umf_assemble', 'umf_blas3_update', 'umf_build_tuples',
             'umf_create_element', 'umf_dump', 'umf_extend_front',
             'umf_garbage_collection', 'umf_get_memory', 'umf_init_front',
             'umf_kernel', 'umf_kernel_init', 'umf_kernel_wrapup',
             'umf_local_search', 'umf_lsolve', 'umf_ltsolve',
             'umf_mem_alloc_element', 'umf_mem_alloc_head_block',
             'umf_mem_alloc_tail_block', 'umf_mem_free_tail_block',
             'umf_mem_init_memoryspace', 'umf_report_vector', 'umf_row_search',
             'umf_scale_column', 'umf_set_stats', 'umf_solve',
             'umf_symbolic_usage', 'umf_transpose', 'umf_tuple_lengths',
             'umf_usolve', 'umf_utsolve', 'umf_valid_numeric',
             'umf_valid_symbolic', 'umf_grow_front', 'umf_start_front',
	     'umf_store_lu', 'umf_scale']
    
    # non-user-callable, int/SuiteSparse_long and real/complex versions:
    UMF = UMF_CREATED + UMFCH

    # user-callable umfpack_*.[ch] files (int/SuiteSparse_long and real/complex):
    UMFPACK = ['umfpack_col_to_triplet', 'umfpack_defaults',
               'umfpack_free_numeric', 'umfpack_free_symbolic',
               'umfpack_get_numeric', 'umfpack_get_lunz',
               'umfpack_get_symbolic', 'umfpack_get_determinant',
               'umfpack_numeric', 'umfpack_qsymbolic', 'umfpack_report_control',
               'umfpack_report_info', 'umfpack_report_matrix',
               'umfpack_report_numeric',
               'umfpack_report_perm',
               'umfpack_report_status', 'umfpack_report_symbolic',
               'umfpack_report_triplet', 'umfpack_report_vector',
               'umfpack_solve', 'umfpack_symbolic', 'umfpack_transpose',
               'umfpack_triplet_to_col', 'umfpack_scale',
               'umfpack_load_numeric', 'umfpack_save_numeric',
               'umfpack_load_symbolic', 'umfpack_save_symbolic']
    
    # user-callable, created from umfpack_solve.c (umfpack_wsolve.h exists, though):
    # with int/SuiteSparse_long and real/complex versions:
    UMFPACKW = ['umfpack_wsolve']

    UMFUSER = UMFPACKW + UMFPACK

    _special_macros = {
        r'umf_[dz][il]_\whsolve': ['CONJUGATE_SOLVE'],
        r'umf_[dz][il]_triplet_map_x': ['DO_MAP', 'DO_VALUES'],
        r'umf_[dz][il]_triplet_map_nox': ['DO_MAP'],
        r'umf_[dz][il]_triplet_nomap_x': ['DO_VALUES'],
        r'umf_[dz][il]_assemble_fixq': ['FIXQ'],
        r'umf_[dz][il]_store_lu_drop': ['DROP'],
        r'umfpack_[dz][il]_wsolve': ['WSOLVE'],
    }

    do_copy = False
    for type_, macro in [('di', ['DINT']),
                         ('dl', ['DLONG']),
                         ('zi', ['ZINT']),
                         ('zl', ['ZLONG'])]:
        for f0 in UMF + UMFUSER:  # TODO: UMFUSER targets not building!
            f = tmp / f'UMFPACK{type_.upper()}/Source/{f0}.c'
            if f0.startswith('umf_'):
                fnew = f.parent / f.name.replace('umf_', f'umf_{type_}_')
            else:
                fnew = f.parent / f.name.replace('umfpack_', f'umfpack_{type_}_')
            # convert targets to correct source files names:
            if 'hsolve' in fnew.name:
                f = f.parent / f.name.replace('hsolve', 'tsolve')
            elif 'umf_triplet' in f0:
                f = f.parent / 'umf_triplet.c'
                do_copy = True
            elif 'assemble' in fnew.name:
                f = f.parent / 'umf_assemble.c'
                do_copy = True
            elif 'store_lu' in fnew.name:
                f = f.parent / 'umf_store_lu.c'
                do_copy = True
            elif 'wsolve':
                f = f.parent / 'umfpack_solve.c'
                do_copy = True
            umfpack_sources.append(str(fnew.relative_to(SS.parent)))
            if not do_copy:
                shutil.move(f, fnew)
            else:
                shutil.copyfile(f, fnew)
                do_copy = False
            # Do any extra macros apply to this file?
            extra_macros = []
            for regex in _special_macros:
                match = re.search(regex, fnew.name)
                if match:
                    extra_macros += _special_macros[regex]
                break
            _add_macros(f=fnew, macros=macro + extra_macros)
            _redirect_headers(f=fnew, headers=umf_hdrs[type_])

    # user-callable, only one version for int/SuiteSparse_long,
    # real/complex, *.[ch] files:
    GENERIC = ['umfpack_timer', 'umfpack_tictoc']
    for f0 in GENERIC:
        f = SS / f'UMFPACK/Source/{f0}.c'
        umfpack_sources.append(str(f.relative_to(SS.parent)))
            
    # UMFPACK
    config.add_library(
        'umfpack',
        sources=umfpack_sources,
        include_dirs=[
            str((tmp / 'UMFPACKI/Source').relative_to(SS.parent)),
            str((tmp / 'UMFPACKL/Source').relative_to(SS.parent)),
            str((tmp / 'UMFPACKDI/Source').relative_to(SS.parent)),
            str((tmp / 'UMFPACKDL/Source').relative_to(SS.parent)),
            str((tmp / 'UMFPACKZI/Source').relative_to(SS.parent)),
            str((tmp / 'UMFPACKZL/Source').relative_to(SS.parent)),
            str((tmp / 'AMDI/Include').relative_to(SS.parent)),
            str((tmp / 'AMDL/Include').relative_to(SS.parent)),
            str((tmp / 'AMDZL/Include').relative_to(SS.parent)),            
            
            str((SS / 'UMFPACK/Include').relative_to(SS.parent)),
            str((SS / 'UMFPACK/Source').relative_to(SS.parent)),
            str((SS / 'AMD/Include').relative_to(SS.parent)),
            str((SS / 'SuiteSparse_config').relative_to(SS.parent)),
            str((SS / 'CHOLMOD/Include').relative_to(SS.parent)),
        ],
        libraries=['amd', 'cholmod', 'suitesparseconfig'],
        language='c')

    # UMFPACK test
    lapack_opt = get_info('lapack')
    config.add_extension(
        'umfpack_demo',
        sources=['umfpack_demo.c'],
        include_dirs=[
            str((SS / 'SuiteSparse_config').relative_to(SS.parent)),
            str((SS / 'AMD/Include').relative_to(SS.parent)),
            str((SS / 'UMFPACK/Include').relative_to(SS.parent)),
        ],
        libraries=['umfpack'],
        language='c',
        extra_info=lapack_opt,
    )
    
    return config


if __name__ == '__main__':
    from numpy.distutils.core import setup

    # Turn on logging of we're in DEBUG mode
    if DEBUG:
        logger.setLevel(logging.INFO)

    # try...finally statement ensures tmp dir is removed at end
    # of setup
    try:
        #if tmp.exists():
        #    logger.info(f'Removing tmp dir {tmp} to start')
        #    shutil.rmtree(tmp)
        #tmp.mkdir()
        setup(**configuration().todict())
    finally:
        if DEBUG:
            logger.info(f'Not removing tmp dir {tmp}')
        else:
            shutil.rmtree(tmp)
