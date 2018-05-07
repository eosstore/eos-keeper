





#### 环境安装


sudo pip install docker sh








docker run -d --restart=always --name nodeos -p 8888:8888 -p 9876:9876 \
    eosio/eos nodeosd.sh --enable-stale-production --producer-name eosio \
    --plugin eosio::chain_api_plugin --plugin eosio::net_api_plugin --http-server-address 0.0.0.0:8888




 nodeos --enable-stale-production --producer-name eosio \
    --http-server-address 0.0.0.0:8889 --p2p-server-address 0.0.0.0:9877 \
    --plugin eosio::chain_api_plugin --plugin eosio::net_api_plugin


for i in `seq 100000`;do echo --$i-- && sleep 1;done > some.log





# Step 1:

docker rm nodeos1 -f

p2p_peer_address=47.104.148.207:9876

private_key=5Hpv9p4krLHRfzMaRtiP2wUuSJx5QErPx1xyVWRddTCDkemH5kK
public_key=EOS6LQ6sGUDNYH35opPHwA1sdw8rjtN9s1ZpF1zA8mgHZQ2xoAgk8


docker run -d --restart=always --name nodeos1 \
    -p 8888:8888 -p 9876:9876 eosio/eos nodeos --resync \
    --plugin eosio::chain_api_plugin \
    --plugin eosio::net_api_plugin \
    --p2p-peer-address $p2p_peer_address \
    --http-server-address 0.0.0.0:8888 \
    --private-key [\"${public_key}\",\"${private_key}\"]


docker logs -f --tail 1 nodeos1

