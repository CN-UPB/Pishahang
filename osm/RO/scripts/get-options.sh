#!/bin/bash

##
# Copyright 2015 Telefónica Investigación y Desarrollo, S.A.U.
# This file is part of openmano
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# For those usages not covered by the Apache License, Version 2.0 please
# contact with: nfvlabs@tid.es
##


#Utility for getting options, must be call with source
#for every <option> it sets a variable 'option_<option>="-"' 
#if the option appears more than once, it concatenates a "-"
#if the option contains an argument: 'option_<option>="argument"'
#if the long option name contains "-" they are converted to "_"
#params that are not options are stored in 'params'
#the options to look for is received in the first argument, 
#a blank separator list with short and long options without the leading - or --
#options to be stored in the same variable must appear in the same word separated by ':'
#insert a trailing = if the option requires an argument
#insert a trailing ? if the option may have an argument NOT IMPLEMENTED
#option -- means get the rest of argument returned as 'option__=$*'

#example: to allow options -h --help -j -k(with argument) --my-long-option(with argument)
# and other parameters after -- provide
#     "help:h j k= my-long-option="
#parsing "-h -karg pepe --my-long-option=otherar -- -s" will set variables
#       option_help="-"
#       option_k="arg"
#       option_my_long_option="otherarg"
#       params=" pepe"
#       option__="-s"


#detect if is called with a source to use the 'exit'/'return' command for exiting
[[ ${BASH_SOURCE[0]} != $0 ]] && ___exit="return" || ___exit="exit"

options="$1"
shift

get_argument=""
#reset variables
params=""
for option_group in $options
do
    _name=${option_group%%:*}
    _name=${_name%=}
    _name=${_name//-/_}
    eval option_${_name}='""'
done

while [[ $# -gt 0 ]]
do
    argument="$1"
    shift
    if [[ -n $get_argument ]]
    then
        [[ ${argument:0:1} == "-" ]] && echo "option '-$option' requires an argument"  >&2 && $___exit 1
        eval ${get_argument}='"$argument"'
        #echo option $get_argument with argument
        get_argument=""
        continue
    fi


    #short options
    if [[ ${argument:0:1} == "-" ]] && [[ ${argument:1:1} != "-" ]] && [[ ${#argument} -ge 2 ]]
    then
        index=0
        while index=$((index+1)) && [[ $index -lt ${#argument} ]]
        do
            option=${argument:$index:1}
            bad_option=y
            for option_group in $options
            do
                _name=""
                for o in $(echo $option_group | tr ":=" " ")
                do
                    [[ -z "$_name" ]] && _name=${o//-/_}
                    #echo option $option versus $o
                    if [[ "$option" == "${o}" ]]
                    then
                        eval option_${_name}='${option_'${_name}'}-'
                        bad_option=n
                        if [[ ${option_group:${#option_group}-1} != "=" ]]
                        then
                            continue
                        fi 
                        if [[ ${#argument} -gt $((index+1)) ]]
                        then
                            eval option_${_name}='"${argument:$((index+1))}"'
                            index=${#argument}
                        else
                            get_argument=option_${_name}
                            #echo next should be argument $argument
                        fi
    
                        break
                    fi
                done
            done
            [[ $bad_option == y ]] && echo "invalid argument '-$option'?  Type -h for help" >&2 && $___exit 1
        done
    elif [[ ${argument:0:2} == "--" ]] && [[ ${#argument} -ge 3 ]]
    then 
        option=${argument:2}
        option_argument=${option#*=}
        option_name=${option%%=*}
        [[ "$option_name" == "$option" ]] && option_argument=""
        bad_option=y
        for option_group in $options
        do
            _name=""
            for o in $(echo $option_group | tr ":=" " ")
            do
                [[ -z "$_name" ]] && _name=${o//-/_}
                #echo option $option versus $o
                if [[ "$option_name" == "${o}" ]]
                then
                    bad_option=n
                    if [[ ${option_group:${#option_group}-1} != "=" ]] 
                    then #not an argument
                        [[ -n "${option_argument}" ]] && echo "option '--${option%%=*}' do not accept an argument " >&2 && $___exit 1
                        eval option_${_name}='"${option_'${_name}'}-"'
                    elif [[ -n "${option_argument}" ]]
                    then
                        eval option_${_name}='"${option_argument}"'
                    else
                        get_argument=option_${_name}
                        #echo next should be argument $argument
                    fi
                    break
                fi
            done
        done
        [[ $bad_option == y ]] && echo "invalid argument '-$option'?  Type -h for help" >&2 && $___exit 1
    elif [[ ${argument:0:2} == "--" ]]
    then
        option__="$*"
        bad_option=y
        for o in $options
        do
            if [[ "$o" == "--" ]]
            then
                bad_option=n
                option__=" $*"
                break
            fi
        done
        [[ $bad_option == y ]] && echo "invalid argument '--'?  Type -h for help" >&2 && $___exit 1
        break
    else
        params="$params ${argument}"
    fi

done

[[ -n "$get_argument" ]] && echo "option '-$option' requires an argument"  >&2 && $___exit 1
$___exit 0
#echo params $params

