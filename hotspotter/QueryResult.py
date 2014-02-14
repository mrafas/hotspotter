from __future__ import division, print_function
from hscom import __common__
(print, print_, print_on, print_off,
 rrr, profile, printDBG) = __common__.init(__name__, '[qr]', DEBUG=False)
# Python
from itertools import izip
from os.path import exists, split, join
from zipfile import error as BadZipFile  # Screwy naming convention.
import os
# Scientific
import numpy as np
# HotSpotter
from hscom import helpers
from hscom import params
from hscom.Printable import DynStruct
import voting_rules2 as vr2


FM_DTYPE  = np.uint32   # Feature Match datatype
FS_DTYPE  = np.float32  # Feature Score datatype
FK_DTYPE  = np.int16    # Feature Position datatype

HASH_LEN = 16

#=========================
# Query Result Class
#=========================


def remove_corrupted_queries(hs, res, dryrun=True):
    # This res must be corrupted!
    query_uid = res.query_uid
    hash_id = helpers.hashstr(query_uid, HASH_LEN)
    qres_dir  = hs.dirs.qres_dir
    testres_dir = join(hs.dirs.cache_dir, 'experiment_harness_results')
    helpers.remove_files_in_dir(testres_dir, dryrun=dryrun)
    helpers.remove_files_in_dir(qres_dir, '*' + query_uid + '*', dryrun=dryrun)
    helpers.remove_files_in_dir(qres_dir, '*' + hash_id + '*', dryrun=dryrun)


def dbg_check_query_result(hs, res, strict=False):
    print('[qr] Debugging result')
    fpath = res.get_fpath(hs)
    print(res)
    print('fpath=%r' % fpath)

    res.true_uid
    qcx = res.qcx
    chip_str = 'q%s' % hs.cidstr(qcx)
    kpts = hs.get_kpts(qcx)
    #
    # Check K are all in bounds
    fk_maxmin = np.array([(fk.max(), fk.min())
                          for fk in res.cx2_fk if len(fk) > 0])
    K = hs.prefs.query_cfg.nn_cfg.K
    assert fk_maxmin.max() < K
    assert fk_maxmin.min() >= 0
    #
    # Check feature indexes are in boundsS
    fx_maxmin = np.array([(fm[:, 0].max(), fm[:, 0].min())
                          for fm in res.cx2_fm if len(fm) > 0])
    nKpts = len(kpts)
    if fx_maxmin.max() >= nKpts:
        msg = ('DBG ERROR: ' + chip_str + ' nKpts=%d max_kpts=%d' % (nKpts, fx_maxmin.max()))
        print(msg)
        if strict:
            raise AssertionError(msg)
    assert fx_maxmin.min() >= 0


def query_result_fpath(hs, qcx, query_uid):
    qres_dir  = hs.dirs.qres_dir
    qcid  = hs.tables.cx2_cid[qcx]
    fname = 'res_%s_qcid=%d.npz' % (query_uid, qcid)
    if len(fname) > 64:
        hash_id = helpers.hashstr(query_uid, HASH_LEN)
        fname = 'res_%s_qcid=%d.npz' % (hash_id, qcid)
    fpath = join(qres_dir, fname)
    return fpath


def query_result_exists(hs, qcx, query_uid):
    fpath = query_result_fpath(hs, qcx, query_uid)
    return exists(fpath)


class QueryResult(DynStruct):
    #__slots__ = ['true_uid', 'qcx', 'query_uid', 'uid', 'title', 'nn_time',
                 #'weight_time', 'filt_time', 'build_time', 'verify_time',
                 #'cx2_fm', 'cx2_fs', 'cx2_fk', 'cx2_score']
    def __init__(res, qcx, uid, qdat=None):
        super(QueryResult, res).__init__()
        res.true_uid  = '' if qdat is None else qdat.get_uid()
        res.qcx       = qcx
        res.query_uid = uid
        res.uid       = uid
        res.title     = uid
        # Assigned features matches
        res.cx2_fm = np.array([], dtype=FM_DTYPE)
        res.cx2_fs = np.array([], dtype=FS_DTYPE)
        res.cx2_fk = np.array([], dtype=FK_DTYPE)
        res.cx2_score = np.array([])
        res.filt2_meta = {}  # messy

    def has_cache(res, hs):
        return query_result_exists(hs, res.qcx)

    def get_fpath(res, hs):
        return query_result_fpath(hs, res.qcx, res.query_uid)

    @profile
    def save(res, hs):
        fpath = res.get_fpath(hs)
        print('[qr] cache save: %r' % (fpath if params.args.verbose_cache
                                       else split(fpath)[1],))
        with open(fpath, 'wb') as file_:
            np.savez(file_, **res.__dict__.copy())
        return True

    @profile
    def load(res, hs):
        'Loads the result from the given database'
        fpath = res.get_fpath(hs)
        qcx_good = res.qcx
        try:
            with open(fpath, 'rb') as file_:
                npz = np.load(file_)
                for _key in npz.files:
                    res.__dict__[_key] = npz[_key]
                npz.close()
            print('[res] res.load() fpath=%r' % (split(fpath)[1],))
            # These are nonarray items even if they are not lists
            # tolist seems to convert them back to their original
            # python representation
            res.qcx = res.qcx.tolist()
            try:
                res.filt2_meta = res.filt2_meta.tolist()
            except AttributeError:
                print('[qr] loading old result format')
                res.filt2_meta = {}
            res.query_uid = str(res.query_uid)
            res.true_uid = res.true_uid.tolist()
            return True
        except IOError as ex:
            #print('[res] encountered IOError: %r' % ex)
            if not exists(fpath):
                print('[res] query result cache miss')
                #print(fpath)
                #print('[res] QueryResult(qcx=%d) does not exist' % res.qcx)
                raise
            else:
                msg = ['[res] QueryResult(qcx=%d) is corrupted' % (res.qcx)]
                msg += ['\n%r' % (ex,)]
                print(''.join(msg))
                raise Exception(msg)
        except BadZipFile as ex:
            print('[res] Caught other BadZipFile: %r' % ex)
            msg = ['[res] Attribute Error: QueryResult(qcx=%d) is corrupted' % (res.qcx)]
            msg += ['\n%r' % (ex,)]
            print(''.join(msg))
            if exists(fpath):
                print('[res] Removing corrupted file: %r' % fpath)
                os.remove(fpath)
                raise IOError(msg)
            else:
                raise Exception(msg)
        except Exception as ex:
            print('Caught other Exception: %r' % ex)
            raise
        res.qcx = qcx_good

    def cache_bytes(res, hs):
        fpath = res.get_fpath(hs)
        return helpers.file_bytes(fpath)

    def get_gt_ranks(res, gt_cxs=None, hs=None):
        'returns the 0 indexed ranking of each groundtruth chip'
        # Ensure correct input
        if gt_cxs is None and hs is None:
            raise Exception('[res] error')
        if gt_cxs is None:
            gt_cxs = hs.get_other_indexed_cxs(res.qcx)
        return res.get_cx_ranks(gt_cxs)

    def get_cx_ranks(res, cx_list):
        cx2_score = res.get_cx2_score()
        top_cxs  = cx2_score.argsort()[::-1]
        foundpos = [np.where(top_cxs == cx)[0] for cx in cx_list]
        ranks_   = [r if len(r) > 0 else [-1] for r in foundpos]
        assert all([len(r) == 1 for r in ranks_])
        rank_list = [r[0] for r in ranks_]
        return rank_list

    def get_cx2_score(res):
        return res.cx2_score

    def get_cx2_fm(res):
        return res.cx2_fm

    def get_cx2_fs(res):
        return res.cx2_fs

    def get_cx2_fk(res):
        return res.cx2_fk

    def get_fmatch_iter(res):
        fmfsfk_enum = enumerate(izip(res.cx2_fm, res.cx2_fs, res.cx2_fk))
        fmatch_iter = ((cx, fx_tup, score, rank)
                       for cx, (fm, fs, fk) in fmfsfk_enum
                       for (fx_tup, score, rank) in izip(fm, fs, fk))
        return fmatch_iter

    def topN_cxs(res, hs, N=None):
        cx2_score = np.array(res.get_cx2_score())
        if hs.prefs.display_cfg.name_scoring:
            cx2_chipscore = np.array(cx2_score)
            cx2_score = vr2.enforce_one_name(hs, cx2_score,
                                             cx2_chipscore=cx2_chipscore)
        top_cxs = cx2_score.argsort()[::-1]
        dcxs_ = set(hs.get_indexed_sample()) - set([res.qcx])
        top_cxs = [cx for cx in iter(top_cxs) if cx in dcxs_]
        #top_cxs = np.intersect1d(top_cxs, hs.get_indexed_sample())
        nIndexed = len(top_cxs)
        if N is None:
            N = hs.prefs.display_cfg.N
        if N == 'all':
            N = nIndexed
        #print('[res] cx2_score = %r' % (cx2_score,))
        #print('[res] returning top_cxs = %r' % (top_cxs,))
        nTop = min(N, nIndexed)
        #print('[res] returning nTop = %r' % (nTop,))
        topN_cxs = top_cxs[0:nTop]
        return topN_cxs

    def show_query(res, hs, **kwargs):
        from hsviz import viz
        print('[res] show_query')
        viz.show_chip(hs, res=res, **kwargs)

    def show_analysis(res, hs, *args, **kwargs):
        from hsviz import viz
        return viz.res_show_analysis(res, hs, *args, **kwargs)

    def show_top(res, hs, *args, **kwargs):
        from hsviz import viz
        return viz.show_top(res, hs, *args, **kwargs)

    def show_gt_matches(res, hs, *args, **kwargs):
        from hsviz import viz
        figtitle = ('q%s -- GroundTruth' % (hs.cidstr(res.qcx)))
        gt_cxs = hs.get_other_indexed_cxs(res.qcx)
        return viz._show_chip_matches(hs, res, gt_cxs=gt_cxs, figtitle=figtitle,
                                      all_kpts=True, *args, **kwargs)

    def show_chipres(res, hs, cx, **kwargs):
        from hsviz import viz
        return viz.res_show_chipres(res, hs, cx, **kwargs)

    def interact_chipres(res, hs, cx, **kwargs):
        from hsviz import interact
        return interact.interact_chipres(hs, res, cx, **kwargs)

    def interact_top_chipres(res, hs, tx, **kwargs):
        from hsviz import interact
        cx = res.topN_cxs(hs, tx + 1)[tx]
        return interact.interact_chipres(hs, res, cx, **kwargs)

    def show_nearest_descriptors(res, hs, qfx, dodraw=True):
        from hsviz import viz
        qcx = res.qcx
        viz.show_nearest_descriptors(hs, qcx, qfx, fnum=None)
        if dodraw:
            viz.draw()

    def get_match_index(res, hs, cx, qfx, strict=True):
        qcx = res.qcx
        fm = res.cx2_fm[cx]
        mx_list = np.where(fm[:, 0] == qfx)[0]
        if len(mx_list) != 1:
            if strict:
                raise IndexError('qfx=%r not found in query %s' %
                                 (qfx, hs.vs_str(qcx, cx)))
            else:
                return None
        else:
            mx = mx_list[0]
            return mx
