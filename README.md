





#### 环境安装


sudo pip install docker sh








docker run -d --restart=always --name nodeos -p 8888:8888 -p 9876:9876 \
    eosio/eos nodeosd.sh --enable-stale-production --producer-name eosio \
    --plugin eosio::chain_api_plugin --plugin eosio::net_api_plugin --http-server-address 0.0.0.0:8888




for i in `seq 100000`;do echo --$i-- && sleep 1;done > some.log