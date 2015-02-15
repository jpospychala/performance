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
  $CURL -X POST -d "$CREATECONTAINER" "$DOHOME/droplets/" >/dev/null
}

case "$CMD" in
  "parallel")
  rm -rf .inqueue*
  ./runner.py -q -d | sort | uniq > .inqueue
  RUNNERS=20
  CHUNKS=400
  LINES=$(cat .inqueue | wc -l)
  ((LINES_PER_CHUNK = (LINES + CHUNKS - 1) / CHUNKS))

  split -l $LINES_PER_CHUNK .inqueue .inqueue.
  for i in `seq $RUNNERS`; do
    ./digitalocean.sh parallelrunner droplet$i > $i.log 2>&1 &
    sleep 1
  done
  ;;

  "parallelrunner")
  while find .inqueue.?? >/dev/null 2>&1; do
    CHUNK=`find .inqueue.?? | head -1`
    mv $CHUNK $CHUNK.$DROPLETNAME
    echo processing $CHUNK.$DROPLETNAME
    ./digitalocean.sh run $DROPLETNAME '' 512mb $CHUNK.$DROPLETNAME
    if [ ! -e "$CHUNK.$DROPLETNAME.tar.gz" ]; then
      echo "processing $CHUNK.$DROPLETNAME failed."
      mv $CHUNK.$DROPLETNAME $CHUNK
    else
      rm $CHUNK.$DROPLETNAME
    fi
  done
  ./digitalocean.sh stop $DROPLETNAME
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
  FILESDIR=filedirs/$$
  mkdir -p $FILESDIR
  cat run.sh | sed "s/#EXTRAARG/$EXTRAARGS/;s/LABEL/digitalocean$SIZE/" > $FILESDIR/run.sh
  if [ -e results/index.json ]; then
    cp results/index.json $FILESDIR/
  fi
  OUTFILE=$ID.tar.gz
  if [ -e "$CFGSTORUN" ]; then
    OUTFILE=$CFGSTORUN.tar.gz
    cp "$CFGSTORUN" $FILESDIR/cfgstorun.txt
  fi
  echo copy files
  TRIES=''
  while ! rsync -ace "ssh -q -oStrictHostKeyChecking=no" $FILESDIR/* "root@$IP:/root"; do
    sleep 20
    TRIES='${TRIES}X'
    if [ "${#TRIES}" -gt 5 ]; then
      echo rsync tries ran out
      exit
    fi
  done
  rm -rf $FILESDIR

  echo executing
  ssh -q -oStrictHostKeyChecking=no "root@$IP" 'bash /root/run.sh'
  echo fetching results
  scp -q -oStrictHostKeyChecking=no "root@$IP:/root/performance/results.tar.gz" $OUTFILE
  ;;

  "stopall")
  for i in `seq 1 20`; do
    ./digitalocean.sh stop droplet$i
  done
  ;;

  "clear")
  rm -rf filedirs
  rm -rf .inqueue*
  rm -rf .curlargs*
  rm -rf *.log
  ;;

  "report")
  for i in .*.tar.gz; do
    echo $i
    tar -zxf $i
    ./report.py results
  done
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
  echo stopping $DROPLETNAME
  GET_DROPLET
  $CURL -X DELETE "$DOHOME/droplets/$ID"
  ;;

  *)
  echo "Unknown command $CMD"
  ;;
esac

rm -rf .curlargs.$$
