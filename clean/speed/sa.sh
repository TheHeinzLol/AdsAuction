#!/usr/bin/env bash
hey -n 2500 -c 150 -m POST -H "X-API-KEY: test_api_key" -T "application/json" -D bodys.txt http://localhost:8002/ad_request_adx_0 &
hey -n 2500 -c 150 -m POST -H "X-API-KEY: test_api_key" -T "application/json" -D bodys.txt http://localhost:8002/ad_request_adx_1 &
hey -n 2500 -c 150 -m POST -H "X-API-KEY: test_api_key" -T "application/json" -D bodys.txt http://localhost:8002/ad_request_adx_2
