#!/usr/bin/env bash

PROJECT=$1
if [ "$PROJECT" == "" ]
then
    echo "Please pass project name parameter"
else
    # origin
    git remote remove origin
    git remote add origin http://server.deephigh.net:7080/deephigh/$PROJECT/server.git
    git push origin master
    git branch --set-upstream-to=origin/master master

    # framework
    git checkout -b framework_$PROJECT \
        && git push origin framework_$PROJECT \
        && git remote add framework http://server.deephigh.net:7080/deephigh/framework/server.git \
        && git checkout master

    find . | grep .py$ | xargs -i sed -e "s/server_env/"$PROJECT"_env/g" -i {}
    find . | grep .py$ | xargs -i sed -e "s/server_user/"$PROJECT"_user/g" -i {}
    find . | grep .py$ | xargs -i sed -e "s/server_network/"$PROJECT"_network/g" -i {}
    find . | grep .py$ | xargs -i sed -e "s/server_local/"$PROJECT"_local/g" -i {}
    find . | grep .py$ | xargs -i sed -e "s/server_db/"$PROJECT"_db/g" -i {}
    find . | grep .py$ | xargs -i sed -e "s/server_web/"$PROJECT"_web/g" -i {}
    find . | grep .py$ | xargs -i sed -e "s/server_cache/"$PROJECT"_cache/g" -i {}
    find . | grep .py$ | xargs -i sed -e "s/\/server\//\/"$PROJECT"\//g" -i {}
    find . | grep .py$ | xargs -i sed -e "s/server_staging_db/"$PROJECT"_staging_db/g" -i {}

    find . | grep .sql$ | xargs -i sed -e "s/server_env/"$PROJECT"_env/g" -i {}
    find . | grep .sql$ | xargs -i sed -e "s/server_user/"$PROJECT"_user/g" -i {}
    find . | grep .sql$ | xargs -i sed -e "s/server_network/"$PROJECT"_network/g" -i {}
    find . | grep .sql$ | xargs -i sed -e "s/server_local/"$PROJECT"_local/g" -i {}
    find . | grep .sql$ | xargs -i sed -e "s/server_db/"$PROJECT"_db/g" -i {}
    find . | grep .sql$ | xargs -i sed -e "s/server_web/"$PROJECT"_web/g" -i {}
    find . | grep .sql$ | xargs -i sed -e "s/server_cache/"$PROJECT"_cache/g" -i {}
    find . | grep .sql$ | xargs -i sed -e "s/server_staging_db/"$PROJECT"_staging_db/g" -i {}

    find . | grep .sh$ | xargs -i sed -e "s/server_env/"$PROJECT"_env/g" -i {}
    find . | grep .sh$ | xargs -i sed -e "s/server_user/"$PROJECT"_user/g" -i {}
    find . | grep .sh$ | xargs -i sed -e "s/server_network/"$PROJECT"_network/g" -i {}
    find . | grep .sh$ | xargs -i sed -e "s/server_local/"$PROJECT"_local/g" -i {}
    find . | grep .sh$ | xargs -i sed -e "s/server_db/"$PROJECT"_db/g" -i {}
    find . | grep .sh$ | xargs -i sed -e "s/server_web/"$PROJECT"_web/g" -i {}
    find . | grep .sh$ | xargs -i sed -e "s/server_cache/"$PROJECT"_cache/g" -i {}
    find . | grep .sh$ | xargs -i sed -e "s/server_staging_db/"$PROJECT"_staging_db/g" -i {}

    git checkout -- myscript/_init_repository.sh
fi
