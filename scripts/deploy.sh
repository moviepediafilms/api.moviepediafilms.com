#! /bin/bash
echo "changing directory" | systemd-cat
cd /home/zeeshan/api.moviepediafilms.com
echo $(pwd) | systemd-cat

echo "git pull" | systemd-cat
/usr/bin/git pull
echo "ok" | systemd-cat

echo "pipenv sync" | systemd-cat
/home/zeeshan/.local/bin/pipenv sync
echo "ok" | systemd-cat
echo "pipenv clean" | systemd-cat
/home/zeeshan/.local/bin/pipenv clean
echo "ok" | systemd-cat

echo "pipenv run python manage.py check --deploy" | systemd-cat
/home/zeeshan/.local/bin/pipenv run python manage.py check --deploy
echo "ok" | systemd-cat

# pipenv run python manage.py migrate --noinput

echo "pipenv run python manage.py collectstatic --noinput" | systemd-cat
/home/zeeshan/.local/bin/pipenv run python manage.py collectstatic --noinput
echo "ok" | systemd-cat

echo "pipenv run python manage.py migrate --noinput" | systemd-cat
/home/zeeshan/.local/bin/pipenv run python manage.py migrate --noinput
echo "ok" | systemd-cat

echo "sudo service api.moviepediafilms restart" | systemd-cat
sudo /usr/sbin/service api.moviepediafilms restart
echo "ok" | systemd-cat
