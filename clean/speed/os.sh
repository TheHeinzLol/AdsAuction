#!/usr/bin/env bash
hey -n 2550 -c 150 -m POST -T "application/json" -D ./bodyo.txt http://localhost:8001/ad_request
