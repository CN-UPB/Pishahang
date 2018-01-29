#!/bin/bash

#This test checks network connection



if ping -q -c 1 -W 1 google.com >/dev/null; then
  #The network is up
  echo 0
else
  #The network is down
  echo 1
fi

