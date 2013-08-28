'''Parameters module:
    stores a bunch of global variables used by the other modules
    It also reads from sys.argv'''
import sys
import os.path
import numpy as np
import helpers
#print('LOAD_MODULE: params.py')

#print(' * __name__ = %s' % __name__)
#print(' * sys.argv = %r' % sys.argv)
#print(' * sys.checkinterval   = %r' % sys.getcheckinterval())
#print(' * sys.defaultencoding = %r' % sys.getdefaultencoding())
#print(' * sys.filesystemencoding = %r' % sys.getfilesystemencoding())
#print(' * sys.prefix = %r' % sys.prefix)

# MODULE GLOBAL VARIABLES
WORK_DIR = 'D:/data/work'
if sys.platform == 'linux2':
    WORK_DIR = '/media/Store/data/work'

# Common databases I use
FROGS     = WORK_DIR+'/FROG_tufts'
JAGUARS   = WORK_DIR+'/JAG_Jaguar_Data'
NAUTS     = WORK_DIR+'/NAUT_Dan'
GZ_ALL    = WORK_DIR+'/GZ_ALL'
WS_HARD   = WORK_DIR+'/WS_hard'
MOTHERS   = WORK_DIR+'/HSDB_zebra_with_mothers'
OXFORD    = WORK_DIR+'/Oxford_Buildings'
PARIS     = WORK_DIR+'/Paris_Buildings'
SONOGRAMS = WORK_DIR+'/sonograms'


DEFAULT = MOTHERS
#DEFAULT = NAUTS
#__BOW_DTYPE__ = np.uint8
__DATABASE__ = NAUTS # TODO: UN__
# Number of processessors
__NUM_PROCS__ = 8 # TODO: UN__


# Feature type to use
__FEAT_TYPE__    = 'HESAFF'
# Matching type
__MATCH_TYPE__   = 'vsmany'

# Number of matches for one-vs-many
__VSMANY_K__     = 5

# Vocab size for bag of words
__BOW_NUM_WORDS__  = long(5e4)

# Thresholds for one-vs-one
__VSONE_RATIO_THRESH__ = 1.5

# SPATIAL RERANK
# Number of top matches to spatially re-rank
__NUM_RERANK__   = 1000
# % diaglen of keypoint extent
__XY_THRESH__    = .1
__SCALE_THRESH__ = .5

hs1_params = {'algorithm':'kdtree',
              'trees'    :4,
              'checks'   :128}

quick_and_dirty_params = {'algorithm':'kdtree',
              'trees'    :8,
              'checks'   :8}

# Unwhitened
mother_hesaff_tuned_params = {'algorithm'          : 'kmeans',
                              'branching'          : 16,
                              'build_weight'       : 0.009999999776482582,
                              'cb_index'           : 0.20000000298023224,
                              'centers_init'       : 'default',
                              'checks'             : 154,
                              'cores'              : 0,
                              'eps'                : 0.0,
                              'iterations'         : 5,
                              'key_size_'          : 20L,
                              'leaf_max_size'      : 4,
                              'log_level'          : 'warning',
                              'max_neighbors'      : -1,
                              'memory_weight'      : 0.0,
                              'multi_probe_level_' : 2L,
                              'random_seed'        : 94222758,
                              'sample_fraction'    : 0.10000000149011612,
                              'sorted'             : 1,
                              'speedup'            : 23.30769157409668,
                              'table_number_'      : 12L,
                              'target_precision'   : 0.8999999761581421,
                              'trees'              : 1}

__BOW_AKMEANS_FLANN_PARAMS__ = {'algorithm':'kdtree',
                                'trees'    :8,
                                'checks'   :64}
__BOW_WORDS_FLANN_PARAMS__   = hs1_params 
__VSMANY_FLANN_PARAMS__      = hs1_params
__VSONE_FLANN_PARAMS__       = hs1_params


__VERBOSE_CACHE__ = False
__VERBOSE_LOAD_DATA__ = False
__VERBOSE_MATCHING__ = True

__CACHE_QUERY__    = True
__REVERIFY_QUERY__ = False
__RESAVE_QUERY__   = False

__WHITEN_FEATS__   = False

__HISTEQ__         = False
__REGION_NORM__    = False
__RANK_EQ__        = False
__LOCAL_EQ__       = False
__MAXCONTRAST__    = False

__CHIP_SQRT_AREA__ = 750

dev_databases = {
    'SONOGRAMS' : SONOGRAMS,
    'JAG'       : JAGUARS,
    'FROGS'     : FROGS,
    'NAUTS'     : NAUTS,
    'GZ_ALL'    : GZ_ALL,
    'WS_HARD'   : WS_HARD,
    'MOTHERS'   : MOTHERS,
    'OXFORD'    : OXFORD,
    'PARIS'     : PARIS}

def param_string():
    global __MATCH_TYPE__
    import re
    param_list = []
    param_list_append = param_list.append
    def has_bad_dependency(key):
        bad_depends1 = (key.find('__BOW') == 0    and __MATCH_TYPE__ != 'bagofwords')
        bad_depends2 = (key.find('__VSMANY') == 0 and __MATCH_TYPE__ != 'vsmany')
        bad_depends3 = (key.find('__VSONE') == 0  and __MATCH_TYPE__ != 'vsone')
        return any([bad_depends1, bad_depends2, bad_depends3])
    for key in globals().iterkeys():
        if re.match('__[A-Z_]*__', key):
            if has_bad_dependency(key): continue
            param_list_append(key + ' = ' + repr(globals()[key]))
    param_str = '\n'.join(param_list)
    return param_str
# -------------------
# Strings corresponding to unique ids used by different files

def get_chip_uid():
    global __CHIP_SQRT_AREA__
    global __HISTEQ__
    global __REGION_NORM__
    global __RANK_EQ__
    global __LOCAL_EQ__
    global __MAXCONTRAST__
    isorig = (__CHIP_SQRT_AREA__ is None or __CHIP_SQRT_AREA__ <= 0)
    histeq = ['','_histeq'][__HISTEQ__]
    myeq = ['','_regnorm'][__REGION_NORM__]
    rankeq = ['','_rankeq'][__RANK_EQ__]
    localeq = ['','_localeq'][__LOCAL_EQ__]
    maxcontrast = ['','_maxcont'][__MAXCONTRAST__]
    resize = ['_szorig', ('_sz%r' % __CHIP_SQRT_AREA__)][not isorig] 
    chip_uid = resize + histeq + myeq + rankeq + localeq + maxcontrast
    return chip_uid

def get_feat_uid():
    global __FEAT_TYPE__
    global __WHITEN_FEATS__
    feat_type = '_'+__FEAT_TYPE__
    whiten = ['','_white'][__WHITEN_FEATS__]
    # depends on chip
    feat_uid = feat_type + whiten + get_chip_uid()
    return feat_uid

def get_matcher_uid():
    global __MATCH_TYPE__
    global __VSMANY_K__
    global __BOW_NUM_WORDS__
    matcher_uid = '_'+__MATCH_TYPE__
    if __MATCH_TYPE__ == 'bagofwords':
        matcher_uid += '_W%d' % __BOW_NUM_WORDS__
    if __MATCH_TYPE__ == 'vsmany':
        matcher_uid += '_k%d' % __VSMANY_K__
    if __MATCH_TYPE__ == 'vsone':
        query_uid += 'rat'+str(__RATIO_THRESH__)
    # depends on feat
    matcher_uid += get_feat_uid()
    return matcher_uid

def get_query_uid():
    query_uid = ''
    query_uid += '_sv'+str(__NUM_RERANK__)+'_'+str(__XY_THRESH__)
    query_uid += get_matcher_uid()
    return query_uid

def get_algo_uid():
    'Unique id for the entire algorithm'
    algo_uid = get_query_uid()
    return algo_uid

# -------------------

def mothers_problem_pairs():
    '''MOTHERS Dataset: difficult (qcx, cx) query/result pairs'''
    #-
    viewpoint \
            = [
        ( 16,  17),
        ( 19,  20),
        ( 73,  71),
        ( 75,  78),
        (108, 112), # query is very dark
        (110, 108),
                ]
    #-
    quality   \
            = [
        (27, 26),   #minor viewpoint
        (52, 53),
        (67, 68),   #stupid hard case (query from 68 to 67 direction is better (start with foal)
        (73, 71),
    ]
    #-
    lighting  \
            = [
        (105, 104),
        ( 49,  50), #brush occlusion on legs
        ( 93,  94),
    ]
    #-
    confused  \
            = [
    ]
    #-
    occluded  \
            = [
        (64,65),
    ]
    #-
    return locals()


# reloads this module when I mess with it
def reload_module():
    import imp
    import sys
    imp.reload(sys.modules[__name__])

if '--histeq' in sys.argv:
    print(' * with histogram equalization')
    __HISTEQ__ = True
if '--regnorm' in sys.argv:
    __REGION_NORM__ = True
if '--rankeq' in sys.argv:
    __RANK_EQ__ = True
if '--norankeq' in sys.argv:
    __RANK_EQ__ = False
if '--localeq' in sys.argv:
    __LOCAL_EQ__ = True
if '--maxcont' in sys.argv:
    __MAXCONTRAST__ = True


if '--whiten' in sys.argv or '--white' in sys.argv:
    print(' * with whitening')
    __WHITEN_FEATS__ = True
if '--vsone' in sys.argv:
    __MATCH_TYPE__ = 'vsone'
if '--vsmany' in sys.argv:
    __MATCH_TYPE__ = 'vsmany'
if '--bagofwords' in sys.argv:
    __MATCH_TYPE__ = 'bagofwords'

if '--cache-query' in sys.argv:
    __CACHE_QUERY__ = True
if '--nocache-query' in sys.argv:
    __CACHE_QUERY__ = False


if '--reverify' in sys.argv:
    __REVERIFY_QUERY__ = True

if '--resave-query' in sys.argv:
    __RESAVE_QUERY__ = True # 4H4X5

if '--print-checks' in sys.argv:
    helpers.__PRINT_CHECKS__ = True

if '--serial' in sys.argv:
    __NUM_PROCS__ = 1

for argv in iter(sys.argv):
    if argv.upper() in dev_databases.keys():
        print('\n'.join([' * Default Database set to:'+argv.upper(),
                         ' * Previously: '+str(DEFAULT)]))
        DEFAULT = dev_databases[argv.upper()]
#print(' * load_data: Default database is: '+str(DEFAULT))

# MAJOR HACKS 
#__FORCE_REQUERY_CX__ = set([0,1])
__FORCE_REQUERY_CX__ = set([])

#print(' ...Finished loading params.py')

if __name__ == '__main__':
    print ('Entering param __main__')
    print ('Param string: ')
    print helpers.indent(param_string())
