Docker-Übung: Shellscripts

Reihenfolge:
./01_setup.sh
./02_build.sh
./03_test_local.sh
./04_tag.sh <dockerhub_user>
./05_push.sh <dockerhub_user>
./06_pull_and_run.sh <dockerhub_user>

Beispiel:
./04_tag.sh maoesluz meinimage 1.0 dl5-hello-world2 2.0
./05_push.sh maoesluz dl5-hello-world2 2.0
./06_pull_and_run.sh maoesluz dl5-hello-world2 2.0
