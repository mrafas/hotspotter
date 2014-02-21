
run_nightly()
{
    python _tests/newdb_test.py
    python _tests/coverage_test.py --db NAUTS
    python _tests/query_test.py --db JAG --qcid 1 --nosteal --noshare
    python _tests/query_test.py --db MOTHERS --qcid 1 --nosteal --noshare

    python _tests/query_test.py --db NAUTS --qcid 1 --nocache-query --nocache-feats --nocache-chips --strict
    python _tests/query_test.py --db JAG --qcid 1 --nocache-query --nocache-feats --nocache-chips --strict
    python _tests/query_test.py --db MOTHERS --qcid 28 --nocache-query --nocache-feats --nocache-chips --strict
}


clean_databases()
{
    python dev.py --db NAUT_DAN --delete-cache 
    python dev.py --db FROG_tufts --delete-cache 
    python dev.py --db WD_Siva --delete-cache 
}

run_experiment()
{
    export TEST_NAME="shortlist_test chipsize_test scale_test"
    export DEV_ARGS="--all-gt-cases --print-colscore -t $TEST_NAME"

    python dev.py --db WD_Siva $DEV_ARGS
    python dev.py --db FROG_tufts $DEV_ARGS
    python dev.py --db NAUTS_DAN $DEV_ARGS
}


run_experiment2()
{
    export TEST_NAME="shortlist_test chipsize_test scale_test"
    export DEV_ARGS="--all-gt-cases --print-colscore -t $TEST_NAME"

    python dev.py --db NAUT_Dan $DEV_ARGS 
    python dev.py --db WD_Siva $DEV_ARGS
    python dev.py --db Frogs $DEV_ARGS
    python dev.py --db GZ $DEV_ARGS
}

run_continuous()
{
    #python _tests/query_test.py
    python _tests/coverage_test.py --db NAUTS
    python _tests/query_test.py --db NAUTS
    #--nocache-query --nocache-feats --nocache-chips --strict
}

export TEST_TYPE="continuous"
# Check to see if nightly specified
if [[ $# -gt 0 ]] ; then
    if [[ "$1" = "nightly" ]] ; then
        export TEST_TYPE="nightly"
    elif [[ "$1" = "continuous" ]] ; then
        export TEST_TYPE="continuous"
    elif [[ "$1" = "experiment" ]] ; then
        export TEST_TYPE="experiment"
    elif [[ "$1" = "cleandb" ]] ; then
        export TEST_TYPE="cleandb"
    fi
fi

echo "TEST_TYPE=$TEST_TYPE"

#normrule_test
if [[ "$TEST_TYPE" = "continuous" ]] ; then
    run_continuous $@
elif [[ "$TEST_TYPE" = "experiment" ]] ; then
    run_experiment2
elif [[ "$TEST_TYPE" = "nightly" ]] ; then
    run_nightly
elif [[ "$TEST_TYPE" = "cleandb" ]] ; then
    clean_databases
fi