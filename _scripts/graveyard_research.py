def precompute_bag_of_words2(hs):
    print('__PRECOMPUTING_BAG_OF_WORDS__')
    # Build (or reload) one vs many flann index
    feat_dir  = hs.dirs.feat_dir
    cache_dir = hs.dirs.cache_dir
    num_clusters = params.__VOCAB_SIZE__
    # Compute words
    ax2_cx, ax2_fx, ax2_desc = aggregate_descriptors_1vM(hs)
    ax2_wx, words = algos.precompute_akmeans(ax2_desc, 
                                             num_clusters,
                                             force_recomp=False, 
                                             cache_dir=cache_dir)
    # Build a NN index for the words
    flann_words = pyflann.FLANN()
    algorithm = 'default'
    flann_words_params = flann_words.build_index(words, algorithm=algorithm)
    print(' * bag of words is using '+linear+' NN search')
    # Compute Inverted File
    wx2_axs = [[] for _ in xrange(num_clusters)]
    for ax, wx in enumerate(ax2_wx):
        wx2_axs[wx].append(ax)
    wx2_cxs = [[ax2_cx[ax] for ax in ax_list] for ax_list in wx2_axs]
    wx2_fxs = [[ax2_fx[ax] for ax in ax_list] for ax_list in wx2_axs]
    # Create visual-word-vectors for each chip
    # Build bow using coorindate list coo matrix
    # The term frequency (TF) is implicit in the coo format
    coo_cols = ax2_wx
    coo_rows = ax2_cx
    coo_values = np.ones(len(ax2_cx), dtype=np.uint8)
    coo_format = (coo_values, (coo_rows, coo_cols))
    coo_cx2_bow = scipy.sparse.coo_matrix(
        coo_format, dtype=np.float, copy=True)
    # Normalize each visual vector
    csr_cx2_bow = scipy.sparse.csr_matrix(coo_cx2_bow, copy=False)
    csr_cx2_bow = sklearn.preprocessing.normalize(
        csr_cx2_bow, norm=BOW_NORM, axis=1, copy=False)
    # Calculate inverse document frequency (IDF)
    # chip indexes (cxs) are the documents
    num_chips = np.float(len(hs.tables.cx2_cid))
    wx2_df  = [len(set(cx_list)) for cx_list in wx2_cxs]
    wx2_idf = np.log2(num_chips / np.array(wx2_df, dtype=np.float))
    wx2_idf.shape = (1, wx2_idf.size)
    # Preweight the bow vectors
    idf_sparse = scipy.sparse.csr_matrix(wx2_idf)
    cx2_bow = scipy.sparse.vstack(
        [row.multiply(idf_sparse) for row in csr_cx2_bow], format='csr')
    # Renormalize
    cx2_bow = sklearn.preprocessing.normalize(
        cx2_bow, norm=BOW_NORM, axis=1, copy=False)
    # Return vocabulary

    wx2_fxs = np.array(wx2_fxs)
    wx2_cxs = np.array(wx2_cxs)
    wx2_idf = np.array(wx2_idf)
    wx2_idf.shape = (wx2_idf.size, )
    vocab = Vocabulary(words, flann_words, cx2_bow, wx2_idf, wx2_cxs, wx2_fxs)
    return vocab

def truncate_vvec(vvec, thresh):
    shape = vvec.shape
    vvec_flat = vvec.toarray().ravel()
    vvec_flat = vvec_flat * (vvec_flat > thresh)
    vvec_trunc = scipy.sparse.csr_matrix(vvec_flat)
    vvec_trunc = sklearn.preprocessing.normalize(
        vvec_trunc, norm=BOW_NORM, axis=1, copy=False)
    return vvec_trunc

def test__():
    vvec_flat = np.array(vvec.toarray()).ravel()
    qcx2_wx   = np.flatnonzero(vvec_flat)
    cx2_score = (cx2_bow.dot(vvec.T)).toarray().ravel()

    cx2_nx = hs.tables.cx2_nx
    qnx = cx2_nx[qcx]
    other_cx, = np.where(cx2_nx == qnx)

    vvec2 = truncate_vvec(vvec, .04)
    vvec2_flat = vvec2.toarray().ravel()

    cx2_score = (cx2_bow.dot(vvec.T)).toarray().ravel()
    top_cxs = cx2_score.argsort()[::-1]

    cx2_score2 = (cx2_bow.dot(vvec2.T)).toarray().ravel()
    top_cxs2 = cx2_score2.argsort()[::-1]

    comp_str = ''
    tst2s2_list = np.vstack([top_cxs, cx2_score, top_cxs2, cx2_score2]).T
    for t, s, t2, s2 in tst2s2_list:
        m1 = [' ', '*'][t in other_cx]
        m2 = [' ', '*'][t2 in other_cx] 
        comp_str += m1 + '%4d %4.2f %4d %4.2f' % (t, s, t2, s2) + m2 + '\n'
    print comp_str
    df2.close_all_figures()
    df2.show_signature(vvec_flat, fignum=2)
    df2.show_signature(vvec2_flat, fignum=3)
    df2.present()
    #df2.show_histogram(qcx2_wx, fignum=1)
    pass

        #_qfs = vvec_flat[wx]
            #_fs = cx2_bow[cx, wx]
            #fs  = _qfs * _fs
    #print helpers.toc(t)


    #t = helpers.tic()
    #cx2_fm = [[] for _ in xrange(len(cx2_cid))]
    #cx2_fs = [[] for _ in xrange(len(cx2_cid))]
    #qfx2_cxlist = wx2_cxs[qfx2_wx] 
    #qfx2_fxlist = wx2_fxs[qfx2_wx] 
    #qfx2_fs = wx2_idf[qfx2_wx] 
    #for qfx, (fs, cx_list, fx_list) in enumerate(zip(qfx2_fs, 
                                                     #qfx2_cxlist, 
                                                     #qfx2_fxlist)):
        #for (cx, fx) in zip(cx_list, fx_list): 
            #if cx == qcx: continue
            #fm  = (qfx, fx)
            #cx2_fm[cx].append(fm)
            #cx2_fs[cx].append(fs)
    #cx2_fm_ = cx2_fm
    #cx2_fs_ = cx2_fs
    #print helpers.toc(t)
    #t = helpers.tic()

# the inverted file (and probably tf-idf scores too)
# Compute word assignments of database descriptors
def __assign_tfidf_vvec(cx2_desc, words, flann_words):
    '''
    Input: cx2_desc 
    Description: 
        Assigns the descriptors in each chip to a visual word
        Makes a sparse vector weighted by chip term frequency
        Compute the iverse document frequency 
    Output: cx2_vvec, wx2_idf
    '''
    # Compute inverse document frequency (IDF)
    num_train = len(train_cxs)
    wx2_idf   = __idf(wx2_cxs, num_train)
    # Preweight the bow vectors
    cx2_vvec  = algos.sparse_multiply_rows(csr_cx2_vvec, wx2_idf)
    # Normalize
    cx2_vvec = algos.sparse_normalize_rows(cx2_vvec)
    return cx2_vvec, wx2_idf

def __compute_vocabulary(hs, train_cxs):
    # hotspotter data
    cx2_cid  = hs.tables.cx2_cid
    cx2_desc = hs.feats.cx2_desc
    # training information
    tx2_cid  = cx2_cid[train_cxs]
    tx2_desc = cx2_desc[train_cxs]



#------------------- convert
@helpers.__DEPRICATED__
def __read_ox_gtfile_OLD(gt_fpath, gt_name, quality):
    ox_chip_info_list = []
    with open(gt_fpath,'r') as file:
        line_list = file.read().splitlines()
        for line in line_list:
            if line == '': continue
            fields = line.split(' ')
            gname = fields[0].replace('oxc1_','')+'.jpg'
            if gname.find('paris_') >= 0: 
                # PARIS HACK >:(
                #Because they just cant keep their paths consistent 
                paris_hack = gname[6:gname.rfind('_')]
                gname = paris_hack+'/'+gname
            if gname in corrupted_gname_list: continue
            if len(fields) > 1: #quality == query
                roi = map(lambda x: int(round(float(x))),fields[1:])
            else: # quality in ['good','ok','junk']
                gpath = os.path.join(img_dpath, gname)
                (w,h) = Image.open(gpath).size
                roi = [0,0,w,h]
            ox_chip_info = (gt_name, gname, roi, quality, gt_fpath)
            ox_chip_info_list.append(ox_chip_info)
    return ox_chip_info_list
                     
@helpers.__DEPRICATED__
def convert_from_oxford_sytle_OLD(db_dir):
    hs_dirs, hs_tables = load_data2.load_csv_tables(db_dir)

    # Get directories for the oxford groundtruth
    oxford_gt_dpath      = join(db_dir, 'oxford_style_gt')
    corrupted_file_fpath = join(db_dir, 'corrupted_files.txt')

    # Check for corrupted files (Looking at your Paris Buildings Dataset)
    corrupted_gname_list = []
    if helpers.checkpath(corrupted_file_fpath):
        with open(corrupted_file_fpath) as f:
            corrupted_gname_list = f.read().splitlines()
        corrupted_gname_list = set(corrupted_gname_list)
    print('Loading Oxford Style Images')

    # Recursively get relative path of all files in img_dpath
    img_dpath  = join(db_dir, 'images')
    gname_list = [join(relpath(root, img_dpath), fname).replace('\\','/').replace('./','')\
                    for (root,dlist,flist) in os.walk(img_dpath)
                    for fname in flist]

    print('Loading Oxford Style Names and Chips')
    # Read the Oxford Style Groundtruth files
    gt_fname_list = os.listdir(oxford_gt_dpath)

    print('There are %d ground truth files' % len(gt_fname_list))
    total_chips = 0
    quality2_nchips = {'good':0,'bad':0,'ok':0,'junk':0,'query':0}
    gtname2_nchips = {}
    qtx2_nchips = []
    ox_chip_info_list = []
    for gt_fname in iter(gt_fname_list):
        #Get gt_name, quality, and num from fname
        (gt_name, quality, num) = __oxgtfile2_oxgt_tup(gt_fname)
        gt_fpath = join(oxford_gt_dpath, gt_fname)
        ox_chip_info_sublist = __read_ox_gtfile_OLD(gt_fpath, gt_name, quality)
        num_subchips = len(ox_chip_info_sublist)
        ox_chip_info_list.extend(ox_chip_info_sublist)
        # Sanity
        # count number of chips
        quality2_nchips[quality] += num_subchips
        total_chips              += num_subchips
        if not gt_name in gtname2_nchips.keys():
            gtname2_nchips[gt_name] = 0
        gtname2_nchips[gt_name] += num_subchips
        qtx2_nchips.append(num_subchips)

    import numpy as np
    print('Total num: %d ' % total_chips)
    print('Quality breakdown: '+repr(quality2_nchips).replace(',',',\n    '))
    print('GtName breakdown: '+repr(gtname2_nchips).replace(',',',\n    '))
    print('Quality Sanity Total %d: ' % np.array(map(int, quality2_nchips.values())).sum())
    print('Gt_Name Sanity Total %d: ' % np.array(map(int, gtname2_nchips.values())).sum())

    gtx2_name  = [tup[0] for tup in iter(ox_chip_info_list)]
    gtx2_gname = [tup[1] for tup in iter(ox_chip_info_list)]

    unique_gnames = set(gtx2_gname)

    print('Total chips: %d ' % len(gtx2_gname))
    print('Unique chip gnames: %d ' % len(unique_gnames))

    gname2_info = {}
    query_images = []
    for (name, gname, roi,  quality, fpath) in iter(ox_chip_info_list):
        if quality == 'query':
            query_images.append(gname)
        if not gname in gname2_info.keys():
            gname2_info[gname] = []
        gname2_info[gname].append((name, quality, roi, fpath))

    for gname in gname2_info.keys():
        info_list = gname2_info[gname]
        print '-------------'
        print '\n    '.join(map(repr, [gname]+info_list))


    print('This part prints out which files the query images exist in')
    import subprocess
    os.chdir(oxford_gt_dpath)
    for qimg in query_images:
        print('-----')
        qimg = qimg.replace('.jpg','')
        cmd = ['grep', qimg, '*.txt']
        cmd2 = ' '.join(cmd)
        os.system(cmd2)

    print('Num query images: ' + str(len(query_images)))
    print('Num unique query images: ' + str(len(set(query_images))))


    print('Total images: %d ' % len(gname_list))
    print('Total unique images: %d ' % len(set(gname_list)))

    len(ox_chip_info_list)
    print '\n'.join((repr(cinfo) for cinfo in iter(ox_chip_info_list)))
    # HACKISH Duplicate detection. Eventually this should actually be in the codebase
    print('Detecting and Removing Duplicate Ground Truth')
    dup_cx_list = []
    for nx in nm.get_valid_nxs():
        cx_list = array(nm.nx2_cx_list[nx])
        gx_list = cm.cx2_gx[cx_list]
        (unique_gx, unique_x) = np.unique(gx_list, return_index=True)
        name = nm.nx2_name[nx]
        for gx in gx_list[unique_x]:
            bit = False
            gname = gm.gx2_gname[gx]
            x_list = pylab.find(gx_list == gx)
            cx_list2  = cx_list[x_list]
            roi_list2 = cm.cx2_roi[cx_list2]
            roi_hash = lambda roi: roi[0]+roi[1]*10000+roi[2]*100000000+roi[3]*1000000000000
            (_, unique_x2) = np.unique(map(roi_hash, roi_list2), return_index=True)
            non_unique_x2 = np.setdiff1d(np.arange(0,len(cx_list2)), unique_x2)
            for nux2 in non_unique_x2:
                cx_  = cx_list2[nux2]
                dup_cx_list += [cx_]
                roi_ = roi_list2[nux2]
                print('Duplicate: cx=%4d, gx=%4d, nx=%4d roi=%r' % (cx_, gx, nx, roi_) )
                print('           Name:%s, Image:%s' % (name, gname) )
                bit = True
            if bit:
                print('-----------------')
    for cx in dup_cx_list:
        cm.remove_chip(cx)

#---------end convert
#@profile
def __spatially_verify(func_homog, kpts1, kpts2, fm, fs, DBG=None):
    '''1) compute a robust transform from img2 -> img1
       2) keep feature matches which are inliers '''
    # ugg transpose, I like row first, but ransac seems not to
    if len(fm) == 0: 
        return (np.empty((0, 2)), np.empty((0, 1)), np.eye(3))
    xy_thresh = params.__XY_THRESH__
    kpts1_m = kpts1[fm[:, 0], :].T
    kpts2_m = kpts2[fm[:, 1], :].T
    # -----------------------------------------------
    # TODO: SHOULD THIS HAPPEN HERE? (ISSUE XY_THRESH)
    # Get match threshold 10% of matching keypoint extent diagonal
    img1_extent = (kpts1_m[0:2, :].max(1) - kpts1_m[0:2, :].min(1))[0:2]
    xy_thresh1_sqrd = np.sum(img1_extent**2) * (xy_thresh**2)
    dodbg = False if DBG is None else __DEBUG__
    if dodbg:
        print('---------------------------------------')
        print('INFO: spatially_verify xy threshold:')
        print(' * Threshold is %.1f%% of diagonal length' % (xy_thresh*100))
        print(' * img1_extent = %r '     % img1_extent)
        print(' * img1_diag_len = %.2f ' % np.sqrt(np.sum(img1_extent**2)))
        print(' * xy_thresh1_sqrd=%.2f'  % np.sqrt(xy_thresh1_sqrd))
        print('---------------------------------------')
    # -----------------------------------------------
    hinlier_tup = func_homog(kpts2_m, kpts1_m, xy_thresh1_sqrd) 
    if dodbg:
        print('  * ===')
        print('  * Found '+str(len(inliers))+' inliers')
        print('  * with transform H='+repr(H))
        print('  * fm.shape = %r fs.shape = %r' % (fm.shape, fs.shape))
    if not hinlier_tup is None:
        H, inliers = hinlier_tup
    else:
        H = np.eye(3)
        inliers = []
    if len(inliers) > 0:
        fm_V = fm[inliers, :]
        fs_V = fs[inliers, :]
    else: 
        fm_V = np.empty((0, 2))
        fs_V = np.array((0, 1))
    return fm_V, fs_V, H

def spatially_verify(kpts1, kpts2, fm, fs, DBG=None):
    ''' Concrete implementation of spatial verification
        using the deterministic ellipse based sample conensus'''
    ransac_func = spatial_verification.H_homog_from_DELSAC
    return __spatially_verify(ransac_func, kpts1, kpts2, fm, fs, DBG)
spatially_verify.__doc__ += '\n'+__spatially_verify.__doc__

#@profile
def match_vsone(desc2, vsone_flann, ratio_thresh=1.2, burst_thresh=None, DBG=False):
    '''
    Matches desc2 vs desc1 using Lowe's ratio test
    Input:
        desc2         - other descriptors (N2xD)
        vsone_flann     - FLANN index of desc1 (query descriptors (N1xD)) 
    Thresholds: 
        ratio_thresh = 1.2 - keep if dist(2)/dist(1) > ratio_thresh
        burst_thresh = 1   - keep if 0 < matching_freq(desc1) <= burst_thresh
    Output: 
        fm - Mx2 array of matching feature indexes
        fs - Mx1 array of matching feature scores '''
    # features to their matching query features
    checks = params.__FLANN_PARAMS__['checks']
    (fx2_qfx, fx2_dist) = vsone_flann.nn_index(desc2, 2, checks=checks)
    # RATIO TEST
    fx2_ratio  = np.divide(fx2_dist[:, 1], fx2_dist[:, 0]+1E-8)
    fx_passratio, = np.where(fx2_ratio > ratio_thresh)
    fx = fx_passratio
    # BURSTINESS TEST
    # Find frequency of descriptor matches
    # Select the query features which only matched < burst_thresh
    # Convert qfx to fx
    # FIXME: there is probably a better way of doing this.
    if not burst_thresh is None:
        qfx2_frequency = np.bincount(fx2_qfx[:, 0])
        qfx_occuring   = qfx2_frequency > 0
        qfx_nonbursty  = qfx2_frequency <= burst_thresh
        qfx_nonbursty_unique, = np.where(
            np.bitwise_and(qfx_occuring, qfx_nonbursty))
        _qfx_set      = set(qfx_nonbursty_unique.tolist())
        fx2_nonbursty = [_qfx in _qfx_set for _qfx in iter(fx2_qfx[:, 0])]
        fx_nonbursty, = np.where(fx2_nonbursty)
        fx  = np.intersect1d(fx, fx_nonbursty, assume_unique=True)
    # RETURN vsone matches and scores
    qfx = fx2_qfx[fx, 0]
    fm  = np.array(zip(qfx, fx))
    fs  = fx2_ratio[fx]
    # DEBUG
    if DBG:
        print('-------------')
        print('Matching vsone:')
        print(' * Ratio threshold: %r ' % ratio_thresh)
        print(' * Burst threshold: %r ' % burst_thresh)
        print(' * fx_passratio.shape   = %r ' % (  fx_passratio.shape, ))
        if not burst_thresh is None:
            print(' * fx_nonbursty.shape   = %r ' % (  fx_nonbursty.shape, ))
        print(' * fx.shape   = %r ' % (  fx.shape, ))
        print(' * qfx.shape  = %r ' % (  qfx.shape, ))
    return (fm, fs)


def default_preferences():
    root = Pref()
    
    pref_feat = Pref()
    pref_feat.kpts_type = Pref(2,choices=['DOG','HESS','HESAFF'])
    pref_feat.desc_type = Pref(0,choices=['SIFT'])

    pref_bow = Pref()
    pref_bow.vocab_size = 1e5

    pref_1v1 = Pref()
    
    pref_1vM = Pref()

def get_nth_truepos_match(res, hs, n, SV):
    truepos_cxs, truepos_ranks, truepos_scores = get_true_matches(res, hs, SV)
    nth_cx    = truepos_cxs[n]
    nth_rank  = truepos_ranks[n]
    nth_score = truepos_scores[n]
    printDBG('Getting the nth=%r true pos cx,rank,score=(%r, %r, %r)' % \
          (n, nth_cx, nth_rank, nth_score))
    return nth_cx, nth_rank, nth_score

def get_nth_falsepos_match(res, hs, n, SV):
    falsepos_cxs, falsepos_ranks, falsepos_scores = get_false_matches(res, hs, SV)
    nth_cx    = falsepos_cxs[n]
    nth_rank  = falsepos_ranks[n]
    nth_score = falsepos_scores[n]
    printDBG('Getting the nth=%r false pos cx,rank,score=(%r, %r, %r)' % \
          (n, nth_cx, nth_rank, nth_score))
    return nth_cx, nth_rank, nth_score

def get_true_positive_ranks(qcx, top_cx, cx2_nx):
    'Returns the ranking of the other chips which should have scored high'
    top_nx = cx2_nx[top_cx]
    qnx    = cx2_nx[qcx]
    _truepos_ranks, = np.where(top_nx == qnx)
    truepos_ranks = _truepos_ranks[top_cx[_truepos_ranks] != qcx]
    falsepos_scores = top_score[falsepos_ranks]
    falsepos_cxs    = top_cx[falsepos_ranks]
    return truepos_ranks

def get_false_positive_ranks(qcx, top_cx, cx2_nx):
    'Returns the ranking of the other chips which should have scored high'
    top_nx = cx2_nx[top_cx]
    qnx    = cx2_nx[qcx]
    _falsepos_ranks, = np.where(top_nx != qnx)
    falsepos_ranks = _falsepos_ranks[top_cx[_falsepos_ranks] != qcx]
    return falsepos_ranks

def get_true_matches(res, hs, SV):
    qcx = res.qcx
    cx2_nx = hs.tables.cx2_nx
    cx2_score, cx2_fm, cx2_fs = res.get_info(SV)
    top_cx = np.argsort(cx2_score)[::-1]
    top_score = cx2_score[top_cx]
    # Get true postive ranks (groundtruth)
    truepos_ranks  = get_true_positive_ranks(qcx, top_cx, cx2_nx)
    truepos_scores = top_score[truepos_ranks]
    truepos_cxs    = top_cx[truepos_ranks]
    return truepos_cxs, truepos_ranks, truepos_scores

def get_false_matches(res, hs, SV):
    qcx = res.qcx
    cx2_nx = hs.tables.cx2_nx
    cx2_score, cx2_fm, cx2_fs = res.get_info(SV)
    top_cx = np.argsort(cx2_score)[::-1]
    top_score = cx2_score[top_cx]
    # Get false postive ranks (non-groundtruth)
    falsepos_ranks  = get_false_positive_ranks(qcx, top_cx, cx2_nx)
    falsepos_scores = top_score[falsepos_ranks]
    falsepos_cxs    = top_cx[falsepos_ranks]

# Score a single query for name consistency
# Written: 5-28-2013 
def res2_name_consistency(hs, res):
    '''Score a single query for name consistency
    Input: 
        res - query result
    Returns: Dict
        error_chip - degree of chip error
        name_error - degree of name error
        gt_pos_name - 
        gt_pos_chip - 
    '''
    # Defaults to -1 if no ground truth is in the top results
    cm, nm = em.hs.get_managers('cm','nm')
    qcx  = res.rr.qcx
    qnid = res.rr.qnid
    qnx   = nm.nid2_nx[qnid]
    ret = {'name_error':-1,      'chip_error':-1,
           'gt_pos_chip':-1,     'gt_pos_name':-1, 
           'chip_precision': -1, 'chip_recall':-1}
    if qnid == nm.UNIDEN_NID: exec('return ret')
    # ----
    # Score Top Chips
    top_cx = res.cx_sort()
    gt_pos_chip_list = (1+pylab.find(qnid == cm.cx2_nid(top_cx)))
    # If a correct chip was in the top results
    # Reward more chips for being in the top X
    if len(gt_pos_chip_list) > 0:
        # Use summation formula sum_i^n i = n(n+1)/2
        ret['gt_pos_chip'] = gt_pos_chip_list.min()
        _N = len(gt_pos_chip_list)
        _SUM_DENOM = float(_N * (_N + 1)) / 2.0
        ret['chip_error'] = float(gt_pos_chip_list.sum())/_SUM_DENOM
    # Calculate Precision / Recall (depends on the # threshold/max_results)
    ground_truth_cxs = np.setdiff1d(np.array(nm.nx2_cx_list[qnx]), np.array([qcx]))
    true_positives  = top_cx[gt_pos_chip_list-1]
    false_positives = np.setdiff1d(top_cx, true_positives)
    false_negatives = np.setdiff1d(ground_truth_cxs, top_cx)

    nTP = float(len(true_positives)) # Correct result
    nFP = float(len(false_positives)) # Unexpected result
    nFN = float(len(false_negatives)) # Missing result
    #nTN = float( # Correct absence of result

    ret['chip_precision'] = nTP / (nTP + nFP)
    ret['chip_recall']    = nTP / (nTP + nFN)
    #ret['true_negative_rate'] = nTN / (nTN + nFP)
    #ret['accuracy'] = (nTP + nFP) / (nTP + nTN + nFP + nFN)
    # ----
    # Score Top Names
    (top_nx, _) = res.nxcx_sort()
    gt_pos_name_list = (1+pylab.find(qnid == nm.nx2_nid[top_nx]))
    # If a correct name was in the top results
    if len(gt_pos_name_list) > 0: 
        ret['gt_pos_name'] = gt_pos_name_list.min() 
        # N should always be 1
        _N = len(gt_pos_name_list)
        _SUM_DENOM = float(_N * (_N + 1)) / 2.0
        ret['name_error'] = float(gt_pos_name_list.sum())/_SUM_DENOM
    # ---- 
    # RETURN RESULTS
    return reteturn falsepos_cxs, falsepos_ranks, falsepos_scores

# From PCV (python computer vision) code
def H_homog_from_points(fp,tp):
    """ Find homography H, such that fp is mapped to tp using the 
        linear DLT method. Points are conditioned automatically.  """
    # condition points (important for numerical reasons)
    # --from points--
    fp_mean = np.mean(fp[:2], axis=1)
    maxstd = np.max(np.std(fp[:2], axis=1)) + 1e-9
    C1 = np.diag([1/maxstd, 1/maxstd, 1]) 
    C1[0:2,2] = -fp_mean[0:2] / maxstd
    fp = np.dot(C1,fp)
    # --to points--
    tp_mean = np.mean(tp[:2], axis=1)
    maxstd = np.max(np.std(tp[:2], axis=1)) + 1e-9
    C2 = np.diag([1/maxstd, 1/maxstd, 1])
    C2[0:2,2] = -tp_mean[0:2] / maxstd
    tp = np.dot(C2,tp)
    # create matrix for linear method, 2 rows for each correspondence pair
    num_matches = fp.shape[1]
    A = np.zeros((2*num_matches,9))
    for i in xrange(num_matches):        
        A[2*i] =   [        -fp[0][i],         -fp[1][i],       -1,
                                    0,                 0,        0,
                    tp[0][i]*fp[0][i], tp[0][i]*fp[1][i], tp[0][i]]

        A[2*i+1] = [                0,                 0,        0,
                            -fp[0][i],         -fp[1][i],       -1,
                    tp[1][i]*fp[0][i], tp[1][i]*fp[1][i], tp[1][i]]
    U,S,V = linalg.svd(A)
    H = V[8].reshape((3,3))    
    # decondition
    H = np.dot(linalg.inv(C2),np.dot(H,C1))
    # normalize and return
    return H / H[2,2]

# From PCV (python computer vision) code
def H_affine_from_points(fp,tp):
    """ Find H, affine transformation, such that tp is affine transf of fp. """
    # condition points
    # --from points--
    fp_mean = np.mean(fp[:2], axis=1)
    maxstd = np.max(np.std(fp[:2], axis=1)) + 1e-9
    C1 = np.diag([1/maxstd, 1/maxstd, 1]) 
    C1[0:2,2] = -fp_mean[0:2] / maxstd
    fp_cond = np.dot(C1,fp)
    # --to points--
    tp_mean = np.mean(tp[:2], axis=1)
    C2 = C1.copy() #must use same scaling for both point sets
    C2[0:2,2] = -tp_mean[0:2] / maxstd
    tp_cond = np.dot(C2, tp)
    # conditioned points have mean zero, so translation is zero
    A = np.concatenate((fp_cond[:2], tp_cond[:2]), axis=0)
    U,S,V = linalg.svd(A.T)
    # create B and C matrices as Hartley-Zisserman (2:nd ed) p 130.
    tmp = V[:2].T
    B = tmp[:2]
    C = tmp[2:4]
    tmp2 = np.concatenate((C.dot(linalg.pinv(B)),np.zeros((2,1))), axis=1) 
    H = np.vstack((tmp2,[0,0,1]))
    # decondition
    H = (linalg.inv(C2)).dot(H.dot(C1))
    return H / H[2,2]
def H_homog_from_PCVSAC(kpts1_m, kpts2_m, xy_thresh_sqrd):
    from PCV.geometry import homography
    'Python Computer Visions Random Sample Consensus'
    # Get xy points
    xy1_m = kpts1_m[0:2,:] 
    xy2_m = kpts2_m[0:2,:] 
    # Homogonize points
    fp = np.vstack([xy1_m, np.ones((1,xy1_m.shape[1]))])
    tp = np.vstack([xy2_m, np.ones((1,xy2_m.shape[1]))])
    # Get match threshold 10% of image diagonal
    # Get RANSAC inliers
    model = homography.RansacModel() 
    try: 
        H, pcv_inliers = homography.H_from_ransac(fp, tp, model, 500, np.sqrt(xy_thresh_sqrd))
    except ValueError as ex:
        printWARN('Warning 221 from H_homog_from_PCVSAC'+repr(ex))
        return np.eye(3), []
    # Convert to the format I'm expecting
    inliers = np.zeros(kpts1_m.shape[1], dtype=bool)
    inliers[pcv_inliers] = True
    return H, inliers

#
def inlier_check(xy1_mAt, xy2_m):
    xy_err_sqrd = sum( np.power(xy1_mAt - xy2_m, 2) , 0)
    _inliers, = np.where(xy_err_sqrd < xy_thresh_sqrd)

#http://jameshensman.wordpress.com/2010/06/14/multiple-matrix-multiplication-in-numpy/
def matrix_from_acd(acd_arr):
    '''
    Input: 3xN array represnting a lower triangular matrix
    Output Nx2x2 array of N, 2x2 lower triangular matrixes
    '''
    num_ells = acd_arr.shape[1]
    a = acd_arr[0]
    c = acd_arr[1]
    b = np.zeros(num_ells)
    d = acd_arr[2]
    abcd_mat = np.rollaxis(np.array([(a, b), (c, d)]),2)
    return abcd_mat

'''
# Define two matrices
A = np.random.randn(100,2,2) # DATA
B = np.random.randn(2,2) # OPERATOR

#Right multiplication (operator on right) 
AB = [a*B for a in A]
#or faster version: 
AB = np.dot(A,B)

Left multiplication  (operator on left)  
#BA = [B*a for a in A]
or faster version: 
#BA = np.transpose(np.dot(np.transpose(A,(0,2,1)),B.T),(0,2,1))
 '''
def right_multiply_H_with_acd(acd_arr, H):
    # AB = np.dot(A,B)
    pass

def left_multiply_H_with_acd(H, acd_arr):
    # (BA).T = A.T B.T
    '''
    acd_H = [(w, x), * [(a, 0),
             (y, z)]    (c, d)] =
            [(w*a+x*c, x*d),
             (y*a+z*c, z*d)]
    x is 0 in our case'''
    [(w,_),(y,z)] = H
    a = acd_arr[0]
    c = acd_arr[1]
    d = acd_arr[2]
    acd_H = np.array([(w*a), (y*a+z*c), (z*d)])
    return acd_H

'''
The determinant of a multiplied matrix is the multiplicatin of determinants
from numpy.linalg import det
A = np.random.randn(2,2)
B = np.random.randn(2,2)
print det(A.dot(B)) 
print det(B.dot(A)) 
print det(A) * det(B)
'''

def H_homog_from_RANSAC(kpts1_m, kpts2_m, xy_thresh_sqrd):
    ' Random Sample Consensus'
    return __H_homog_from(kpts1_m, kpts2_m, xy_thresh_sqrd, aff_inliers_from_randomsac)


def aff_inliers_from_randomsac(kpts1_m, kpts2_m, xy_thresh_sqrd, nIter=500, nSamp=3):
    best_inliers = []
    xy1_m    = kpts1_m[0:2,:] # keypoint xy coordinates matches
    xy2_m    = kpts2_m[0:2,:]
    num_m = xy1_m.shape[1]
    match_indexes = np.arange(0,num_m)
    xyz1_m = _homogonize_pts(xy1_m)
    xyz2_m = _homogonize_pts(xy2_m)
    for iterx in xrange(nIter):
        np.random.shuffle(match_indexes)
        selx = match_indexes[:nSamp]
        fp = xyz1_m[:,selx]
        tp = xyz2_m[:,selx]
        # TODO Use cv2.getAffineTransformation
        H_aff12  = H_affine_from_points(fp, tp)
        # Transform XY-Positions
        xyz1_mAt = H_aff12.dot(xyz1_m)  
        xy_err_sqrd = sum( np.power(xyz1_mAt - xyz2_m, 2) , 0)
        _inliers, = np.where(xy_err_sqrd < xy_thresh_sqrd)
        # See if more inliers than previous best
        if len(_inliers) > len(best_inliers):
            best_inliers = _inliers
    return best_inliers

# GRAVEYARD
'''
    __DBG_INFO__ = False

    if __DBG_INFO__:
        cx2_chip_sf = [(w/wt, h/ht)
                    for ((w,h),(wt,ht)) in zip(cx2_imgchip_sz, cx2_chip_sz)]
        cx2_sf_ave = [(sf1 + sf2) / 2 for (sf1, sf2) in cx2_chip_sf]
        cx2_sf_err = [np.abs(sf1 - sf2) for (sf1, sf2) in cx2_chip_sf]
        myprint(mystats(cx2_sf_ave),lbl='ave scale factor')
        myprint(mystats(cx2_sf_err),lbl='ave scale factor error')
'''

            #print('kpts = %r' % len(kpts_mem_use) / 5.0)
            #print('#desc = %r' % len(desc_mem_use) / 128.0)

        #cx2_feats = [load_features(feat_path) for feat_path in iter(cx2_feat_path)]
        #cx2_kpts  = [k for (k,d) in cx2_feats]
        #cx2_desc  = np.array([d for (k,d) in cx2_feats])
        # Whiten descriptors

# ---------
# feature_compute2.py

            #print (' * Stacking '+str(len(cx2_desc))+' features')
            #print helpers.info(cx2_desc, 'cx2_desc')

            #print (' * '+helpers.info(ax2_desc, 'ax2_desc'))
            #print (' * '+helpers.info(ax2_desc_white, 'ax2_desc_white'))

            #print ('Looping through '+str(len(cx2_desc))+' features')

                #print ('index=%r ; offset=%r ; new_desc.shape=%r' % (offset, index, helpers.info(new_desc,'new_desc')))

            #print ('index=%r ; offset=%r ; new_desc.shape=%r' % (index, offset, new_desc.shape,))
            #print ' * '+helpers.info(cx2_desc, 'cx2_desc')

    #if __WHITEN_INDIVIDUAL__: # I dont think this is the way to go
    #    cx2_desc = [algos.whiten(d) for (k,d) in cx2_feats]
    # cache the data



# Memory erro stfuff
            desc_mem_use = 0
            import draw_func2 as df2
            #exec(df2.present())
            kpts_bits, num_kpts, _ = helpers.numpy_list_num_bits(cx2_kpts, np.float32, 5)
            desc_bits, num_desc, _ = helpers.numpy_list_num_bits(cx2_desc, np.uint8, 128)
            print('#kpts = %r ; bits(kpts)=%r ; MB(kpts)=%r' % (num_kpts,
                                                                kpts_bits,
                                                                kpts_bits / 8 / 2.0**20))
            print('#desc = %r ; bits(desc)=%r ; MB(desc)=%r' % (num_desc,
                                                                desc_bits,
                                                                desc_bits / 8 / 2.0**20))
            while True:
                cmd = raw_input('enter debug command (quit to exit)')
                if cmd == 'quit': 
                    break
                exec(cmd)


        # Load features (with single thread!)
        #cx2_feats = parallel_compute(load_features, [cx2_feat_path], num_procs=1)
def printDEBUG(msg):
    print msg



def idontknowwhatiwasdoingwheniwrotethis():
    # Database descriptor + keypoints
    cx2_desc = hs.feats.cx2_desc
    cx2_kpts = hs.feats.cx2_kpts
    cx2_rchip_size = hs.get_cx2_rchip_size()
    def get_features(cx):
        rchip = hs.get_chip(cx)
        rchip_size = cx2_rchip_size[cx]
        fx2_kp     = cx2_kpts[cx]
        fx2_scale  = sv2.keypoint_scale(fx2_kp)
        fx2_desc   = cx2_desc[cx]
        return rchip, rchip_size, fx2_kp, fx2_scale, fx2_desc
    cx = ocxs[0]
    # Grab features
    rchip1, rchip_size1, fx2_kp1, fx2_scale1, fx2_desc1 = get_features(qcx)
    rchip2, rchip_size2, fx2_kp2, fx2_scale2, fx2_desc2 = get_features(cx)
    # Vsmany index
    #c2.precompute_index_vsmany(hs)
    #qcx2_res = mc2.run_matching(hs)

    '''
    bad_consecutive_reranks = 0
    max_bad_consecutive_reranks = 20 # stop if more than 20 bad reranks
    __OVERRIDE__ = False
    '''
        '''
        if __OVERRIDE__ and len(fm_V) == 0:
            bad_consecutive_reranks += 1
            if bad_consecutive_reranks > max_bad_consecutive_reranks:
                print('[mc2] Too many bad consecutive spatial verifications')
                break
        else: 
            bad_consecutive_reranks = 0
        '''

def bad_optimization
    import scipy.optimize
    infintum = np.zeros(num_cands)
    out = np.linalg.lstsq(PLmatrix, infintum)
    I = np.eye(num_cands)
    M = PLmatrix
    def gPL(gamma):
        g = M.dot(gamma)
        return g.T.dot(I).dot(g)
    prior =  np.ones(num_cands)/np.sqrt(num_cands)
    #http://stackoverflow.com/questions/19648408/im-having-difficulty-understanding-the-syntax-of-scipy-optimize?noredirect=1#comment29175764_19648408
    scipy.optimize.minimize(gPL, 
    x, f, d = scipy.optimize.fmin_l_bfgs_b(gPL, prior)
    #gamma, rnorm = scipy.optimize.nnls(PLmatrix, -prior)
    x, residuals, rank, s = scipy.linalg.lstsq(PLmatrix, prior)
    print('gamma=%r' % gamma)
    print('rnorm=%r' % rnorm)

    from sklearn.linear_model import Ridge
    clf = Ridge(alpha=1.0)
    clf.fit(PLmatrix, np.ones(num_cands))
    # L2-normalize rows
    #for rowx in xrange(len(PLmatrix)):
        #PLmatrix[rowx] /= (PLmatrix[rowx]**2).sum()**(.5)

    gamma = np.linalg.solve(PLmatrix, infintum)

def bad_optimization
    import scipy.optimize
    infintum = np.zeros(num_cands)
    out = np.linalg.lstsq(PLmatrix, infintum)
    I = np.eye(num_cands)
    M = PLmatrix
    def gPL(gamma):
        g = M.dot(gamma)
        return g.T.dot(I).dot(g)
    prior =  np.ones(num_cands)/np.sqrt(num_cands)
    #http://stackoverflow.com/questions/19648408/im-having-difficulty-understanding-the-syntax-of-scipy-optimize?noredirect=1#comment29175764_19648408
    scipy.optimize.minimize(gPL, 
    x, f, d = scipy.optimize.fmin_l_bfgs_b(gPL, prior)
    #gamma, rnorm = scipy.optimize.nnls(PLmatrix, -prior)
    x, residuals, rank, s = scipy.linalg.lstsq(PLmatrix, prior)
    print('gamma=%r' % gamma)
    print('rnorm=%r' % rnorm)

    from sklearn.linear_model import Ridge
    clf = Ridge(alpha=1.0)
    clf.fit(PLmatrix, np.ones(num_cands))
    # L2-normalize rows
    #for rowx in xrange(len(PLmatrix)):
        #PLmatrix[rowx] /= (PLmatrix[rowx]**2).sum()**(.5)

    gamma = np.linalg.solve(PLmatrix, infintum)

# From DF2
'''
def save(fig, fpath=None):
    if fpath is None:
        # Find the title
        fpath = fig.canvas.get_window_title()
    if fpath is None: 
        fpath = 'Figure'+str(fig.number)+'.png'
    # Sanatize the filename
    fpath_clean = sanatize_img_fpath(fpath)
    print('[df2] Saving figure to: '+repr(fpath_clean))
    #fig.savefig(fpath_clean, dpi=DPI)
    fig.savefig(fpath_clean, dpi=DPI, bbox_inches='tight')
'''


# adapted from:
# http://jayrambhia.com/blog/sift-keypoint-matching-using-python-opencv/
def draw_matches(rchip1, rchip2, kpts1, kpts2, fm12, vert=False):
    global LINE_COLOR
    h1, w1 = rchip1.shape[0:2]
    h2, w2 = rchip2.shape[0:2]
    woff = 0; hoff = 0 # offsets 
    if vert:
        wB = max(w1, w2); hB = h1+h2; hoff = h1
    else: 
        hB = max(h1, h2); wB = w1+w2; woff = w1
    # Concat images
    match_img = np.zeros((hB, wB, 3), np.uint8)
    match_img[0:h1, 0:w1, :] = rchip1
    match_img[hoff:(hoff+h2), woff:(woff+w2), :] = rchip2
    # Draw lines
    for kx1, kx2 in iter(fm12):
        pt1 = (int(kpts1[kx1,0]),      int(kpts1[kx1,1]))
        pt2 = (int(kpts2[kx2,0])+woff, int(kpts2[kx2,1])+hoff)
        match_img = cv2.line(match_img, pt1, pt2, LINE_COLOR*255)
    return match_img

#def fix_cx2_fm_shape(cx2_fm):
    #for cx in xrange(len(cx2_fm)):
        #fm = cx2_fm[cx]
        #if type(fm) != np.ndarray() or fm.dtype != FM_DTYPE:
            #fm = np.array(fm, dtype=FM_DTYPE)
        #if len(fm.shape) != 2 or fm.shape[1] != 2:
            #fm = fm.reshape(len(fm), 2)
        #cx2_fm[cx] = fm
    #cx2_fm = np.array(cx2_fm)
    #return cx2_fm

def cv2_match(desc1, desc2):
    K = 1
    cv2_matcher = cv2.DescriptorMatcher_create('BruteForce-Hamming')
    raw_matches = cv2_matcher.knnMatch(desc1, desc2, K)
    matches = [(m1.trainIdx, m1.queryIdx) for m1 in raw_matches]




'''
PRIORITY 1: 
* CREATE A SIMPLE TEST DATABASE
* Need simple testcases showing the validity of each step. Do this with a small
* database of three images: Query, TrueMatch, FalseMatch
* Manually remove a selection of keypoints. 

PRIORITY 2: 
* FIX QUERY CACHING
 QueryResult should save each step of the query. 
 * Initial Nearest Neighbors Result,
 * Filter Reciprocal Result
 * Filter Spatial Result
 * Filter Spatial Verification Result 
 You should have the ability to turn the caching of any part off. 

PRIORITY 3: 
 * Unifty vsone and vsmany
 * Just make a query params object
 they are the same process which accepts the parameters: 
     invert_query, qcxs, dcxs
'''
'''
def doit():
    df2.rrr()
    df2.reset()
    res.show_query(hs, SV=False)
    res.show_topN(hs, SV=False)
    df2.update()
    df2.bring_to_front(df2.plt.gcf())
'''
