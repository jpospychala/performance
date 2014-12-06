DROPLETNAME=example.com

DOHOME="https://api.digitalocean.com/v2"
CT="Content-Type: application/json"
AUTH="Authorization: Bearer $DOTOKEN"

SSHKEYS=`curl -s -H "$CT" -H "$AUTH" -X GET "$DOHOME/account/keys" | R path ssh_keys | R map path fingerprint`

CREATECONTAINER=`cat <<EOF
{
  "name":"$DROPLETNAME",
  "region":"nyc3",
  "size":"512mb",
  "image":"ubuntu-14-04-x64",
  "ssh_keys":$SSHKEYS,
  "backups":false,
  "ipv6":true,
  "user_data":null,
  "private_networking":null}
EOF`

function GET_DROPLET {
  DROPLET=`curl -s -H "$CT" -H "$AUTH" -X GET "$DOHOME/droplets/" | \
  R path droplets | \
  R find where "{\"name\": \"$DROPLETNAME\"}"`

  export IP=`echo $DROPLET | R path networks.v4.0.ip_address`
  export ID=`echo $DROPLET | R path id`
  echo "dropet id: $ID ip: $IP"
}

GET_DROPLET

if [ -z "$ID" ]; then
  echo create droplet!
  curl -H "$CT" -H "$AUTH" -X POST -d "$CREATECONTAINER" "$DOHOME/droplets/"

  while [ -z "$IP" ]; do
    GET_DROPLET
  done
fi

# execute
ssh "root@$IP" 'bash -s' < run.sh
scp "root@$IP:/root/performance/report/result.json" $IP.json
# delete droplet
curl -H "$CT" -H "$AUTH" -X DELETE "$DOHOME/droplets/$ID"
