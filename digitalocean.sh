#!/bin/bash
# this script gets or creates smallest DO droplet and remotely executes script on it
# afterwards, droplet is destroyed

if [ -z "$DOTOKEN" ]; then
  echo 'Error: Variable $DOTOKEN with digitalocean API token is not set.'
  exit 1
fi

CMD=$1
DROPLETNAME=$2
EXTRAARGS=$3
SIZE=$4
CFGSTORUN=$5

if [ -z "$DROPLETNAME" ]; then
  DROPLETNAME=perftests
fi
if [ -z "$SIZE" ]; then
  SIZE=512mb
fi
DOHOME="https://api.digitalocean.com/v2"

cat <<EOF > .curlargs.$$
-s
-H "Authorization: Bearer $DOTOKEN"
-H "Content-Type: application/json"
EOF
CURL="curl -K .curlargs.$$"

function GET_DROPLET {
  DROPLET=`$CURL "$DOHOME/droplets/" | \
  R path droplets | \
  R find where "{\"name\": \"$DROPLETNAME\"}"`

  export IP=`R path networks.v4.0.ip_address <<< $DROPLET`
  export ID=`R path id <<< $DROPLET`
}

function CREATE_DROPLET {
  SSHKEYS=`$CURL "$DOHOME/account/keys" | R path ssh_keys | R map path fingerprint`

  CREATECONTAINER=`cat <<EOF
  {
    "name":"$DROPLETNAME",
    "region":"nyc3",
    "size":"$SIZE",
    "image":"ubuntu-14-04-x64",
    "ssh_keys":$SSHKEYS}
EOF`
  $CURL -X POST -d "$CREATECONTAINER" "$DOHOME/droplets/"
}

case "$CMD" in
  "parallel")
  rm -rf .inqueue*
  ./runner.py -q -d sleep_node | sort | uniq > .inqueue
  RUNNERS=1
  LINES=$(cat .inqueue | wc -l)
  ((LINES_PER_RUNNER = (LINES + RUNNERS - 1) / RUNNERS))

  split -l $LINES_PER_RUNNER .inqueue .inqueue.
  for i in .inqueue.*; do
    echo run $i
    ./digitalocean.sh run droplet$i "" 512mb $i | tee $i.log &
  done
  ;;

  "run")

  GET_DROPLET

  if [ -z "$ID" ]; then
    echo "Droplet \"$DROPLETNAME\" not found. Creating..."
    CREATE_DROPLET

    while [ -z "$IP" ]; do
      GET_DROPLET
    done
  fi

  # execute
  if [ -e results/index.json ]; then
    scp -oStrictHostKeyChecking=no results/index.json "root@$IP:/root/index.json"
  fi
  if [ -e "$CFGSTORUN" ]; then
    scp -oStrictHostKeyChecking=no $CFGSTORUN "root@$IP:/root/cfgstorun.txt"
  fi
  cat run.sh | sed "s/#EXTRAARG/$EXTRAARGS/;s/digitalocean512/digitalocean$SIZE/" | ssh -oStrictHostKeyChecking=no "root@$IP" 'bash -s'
  scp -r -oStrictHostKeyChecking=no "root@$IP:/root/performance/results.tar.gz" $ID.tar.gz
  tar -zxvf $ID.tar.gz
  #./digitalocean.sh stop "$DROPLETNAME"
  #./report.py results
  ;;

  "status")
  GET_DROPLET
  if [ -z "$IP" ]; then
    echo "Droplet \"$DROPLETNAME\" not found"
  else
    echo "IP: $IP ID: $ID"
  fi
  ;;

  "ssh")
  GET_DROPLET
  ssh -oStrictHostKeyChecking=no "root@$IP"
  ;;

  "stop")
  GET_DROPLET
  $CURL -X DELETE "$DOHOME/droplets/$ID"
  ;;

  *)
  echo "Unknown command $1"
  ;;
esac

rm .curlargs.$$
