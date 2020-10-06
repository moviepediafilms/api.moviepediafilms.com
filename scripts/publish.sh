#! /bin/bash

curl=/usr/bin/curl

GITHUB_USER=zkhan93
CURR_BRANCH=$(git rev-parse --abbrev-ref HEAD)
GITHUB_REPO=moviepediafilms/api.moviepediafilms.com
GITHUB_TOKEN=$GITHUB_TOKEN
TMP_REQ=/tmp/create_pr_req.json
TMP_RES=/tmp/create_pr_res.json
TMP_MERGE_RES=/tmp/merge_res.json

clean() {

    if [ ${1:-1} -eq 1 ]; then
        echo "cleaning request and response files"
        rm $TMP_REQ
        rm $TMP_RES
        rm $TMP_MERGE_RES
    else
        cat $TMP_RES
    fi
}

merge() {
    PR_NUMBER=$(eval "/usr/bin/jshon -e number -u <$TMP_RES")
    GITHUB_MERGE_LINK=https://api.github.com/repos/$GITHUB_REPO/pulls/$PR_NUMBER/merge
    data="{\"pull_number\":\"$PR_NUMBER\"}"
    curl -X PUT -H "Content-Type: application/json" -d $data -u $GITHUB_USER:$GITHUB_TOKEN $GITHUB_MERGE_LINK -o $TMP_MERGE_RES &>/dev/null
    if [ -f $TMP_MERGE_RES ]; then
        jshon -e message -u <$TMP_MERGE_RES
    else
        echo "merge request to GitHub failed"
    fi
}

raise_pr() {
    DATA="{\"base\": \"master\",
       \"head\":\"${CURR_BRANCH}\",
       \"title\":\"Automatic PR\",
       \"body\":\"PR raised by publish.sh\"}"
    echo $DATA >$TMP_REQ
    GITHUB_PR_LINK=https://api.github.com/repos/$GITHUB_REPO/pulls
    curl -X POST -H "Content-Type: application/json" -d @$TMP_REQ -u $GITHUB_USER:$GITHUB_TOKEN $GITHUB_PR_LINK -o $TMP_RES &>/dev/null

    /usr/bin/jshon -e errors -t <$TMP_RES &>/dev/null
    if [ $? -eq 0 ]; then
        /usr/bin/jshon -e errors -e 0 -e message -u <$TMP_RES
        echo 'Failed to create PR'
    else
        /usr/bin/jshon -e html_url -u <$TMP_RES
        echo 'PR Created successfully'
        merge
    fi
}

clean
raise_pr
