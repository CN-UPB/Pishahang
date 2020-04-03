#!/bin/bash

pid=`ps aux | grep adaptor | awk '{print $2}'`
kill -9 $pid
