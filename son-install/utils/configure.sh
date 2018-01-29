#!/bin/bash
#                            __                    ____
#    _________  ____  ____ _/ /_____ _      ____  / __/   __
#   / ___/ __ \/ __ \/ __ `/ __/ __ `/_____/ __ \/ /_| | / /
#  (__  ) /_/ / / / / /_/ / /_/ /_/ /_____/ / / / __/| |/ /
# /____/\____/_/ /_/\__,_/\__/\__,_/     /_/ /_/_/   |___/
#
#
# This is the SONATA VIM/WIM Configuration tool.
# TODO:
# * Check the user input
# * Delete the temporary files
# * Improve the information provided to the user

HEIGHT=15
WIDTH=40
CHOICE_HEIGHT=7
BACKTITLE="SONATA-NFV"
TITLE="SONATA-NFV VIM WIM CONFIGURATION"
MENU="Choose one of the following options:"

OPTIONS=(1 "LIST VIMs"
         2 "LIST WIMs"
         3 "INSERT VIM"
	 4 "INSERT WIM"
	 5 "DELETE VIM"
	 6 "DELETE WIM"
	 7 "QUIT")

while :
do

CHOICE=$(dialog --clear \
		--nocancel \
                --backtitle "$BACKTITLE" \
                --title "$TITLE" \
                --menu "$MENU" \
                $HEIGHT $WIDTH $CHOICE_HEIGHT \
                "${OPTIONS[@]}" \
                2>&1 >/dev/tty)

case $CHOICE in
        1)
	    dialog --title "List of VIMs" --no-collapse --msgbox "`echo COMPUTE; docker exec -t son-postgres psql -h localhost -U postgres -d vimregistry -c \"SELECT uuid, vendor, type, endpoint FROM VIM WHERE type='compute'\"; echo NETWORKING; docker exec -t son-postgres psql -h localhost -U postgres -d vimregistry -c \"SELECT uuid, vendor, type, endpoint FROM VIM WHERE type='network'\"; echo LINKS;  docker exec -t son-postgres psql -h localhost -U postgres -d vimregistry -c \"SELECT * FROM LINK_VIM \";`" 25 85
            ;;
        2)
	    dialog --title "List of WIMs" --no-collapse --msgbox "`docker exec -t son-postgres psql -h localhost -U postgres -d wimregistry -c \"SELECT uuid, vendor, type, endpoint FROM WIM \";`" 15 85
            ;;
        3)
	    dialog --title "VIM Configuration" --no-cancel --inputbox "Please enter the endpoint ip address.\nExample: 10.100.32.200" 10 60 2> /tmp/endpoint_ip
	    dialog --title "VIM Configuration" --no-cancel --inputbox "Please enter the endpoint username.\nExample: admin" 10 60 2> /tmp/endpoint_user
	    dialog --title "VIM Configuration" --no-cancel --insecure --passwordbox "Please enter the endpoint password.\nExample: adminpass" 10 60 2> /tmp/endpoint_passwd
	    dialog --title "VIM Configuration" --no-cancel --inputbox "Please enter the endpoint tenant name.\nExample: admin" 10 60 2> /tmp/endpoint_tenant_user
	    dialog --title "VIM Configuration" --no-cancel --inputbox "Please enter the endpoint tenant external net uuid.\nThis is the UUID of the public network in the provided tenant/project that is used to provide floating IP addresses.\nExample: cbc5a4fa-59ed-4ec1-ad2d-adb270e21693" 10 90 2> /tmp/endpoint_external_net_uuid
	    dialog --title "VIM Configuration" --no-cancel --inputbox "Please enter the endpoint tenant external router uuid.\nThis is the UUID of the Neutron Router used as gateway toward the external network by the networks of the provided tenant/project.\nExample: cbc5a4fa-59ed-4ec1-ad2d-adb270e21693" 10 90 2> /tmp/endpoint_external_router_uuid
	    ip=$(cat /tmp/endpoint_ip)
            user=$(cat /tmp/endpoint_user)
            passwd=$(cat /tmp/endpoint_passwd)
            tenant_name=$(cat /tmp/endpoint_tenant_user)
            tenant_ext_net=$(cat /tmp/endpoint_external_net_uuid)
            tenant_ext_router=$(cat /tmp/endpoint_external_router_uuid)
            uuid_compute=$(uuidgen)
            uuid_network=$(uuidgen)
	    docker exec -t son-postgres psql -h localhost -U postgres -d vimregistry -c "INSERT INTO VIM (uuid, type, vendor, endpoint, username, tenant, tenant_ext_net, tenant_ext_router, pass, authkey) VALUES ('$uuid_compute', 'compute', 'Heat', '$ip', '$user', '$tenant_name', '$tenant_ext_net', '$tenant_ext_router', '$passwd', null);" > /dev/null
	    docker exec -t son-postgres psql -h localhost -U postgres -d vimregistry -c "INSERT INTO VIM (uuid, type, vendor, endpoint, username, tenant, tenant_ext_net, tenant_ext_router, pass, authkey) VALUES ('$uuid_network', 'network', 'odl', '$ip', '$user', '$tenant_name', null, null, '$passwd', null);" > /dev/null
            docker exec -t son-postgres psql -h localhost -U postgres -d vimregistry -c "INSERT INTO LINK_VIM (COMPUTE_UUID, NETWORKING_UUID) VALUES ('$uuid_compute', '$uuid_network');" > /dev/null
	    dialog --title "VIM Configuration" --msgbox "VIM was added" 6 50
            ;;
        4)
	    dialog --title "WIM Configuration" --no-cancel --inputbox "Please enter the WIM endpoint ip address.\nExample: 10.100.32.200" 10 60 2> /tmp/wim_endpoint_ip
	    dialog --title "WIM Configuration" --no-cancel --inputbox "Please enter the WIM endpoint username.\nExample: admin" 10 60 2> /tmp/wim_endpoint_user
	    dialog --title "WIM Configuration" --no-cancel --insecure --passwordbox "Please enter the WIM endpoint password.\nExample: adminpass" 10 60 2> /tmp/wim_endpoint_passwd
	    dialog --title "WIM Configuration" --no-cancel --inputbox "Please enter the WIM network segment uuid.\nList of CIDR( network prefix and netmask length in the format x.x.x.x/n) separed by space, that are served by the WIM\nExample: 10.0.0.0/14,192.168.0.0/24" 10 90 2> /tmp/wim_net_seg
            wim_ip=$(cat /tmp/wim_endpoint_ip)
            wim_user=$(cat /tmp/wim_endpoint_user)
            wim_passwd=$(cat /tmp/wim_endpoint_passwd)
            wim_net_seg=$(cat /tmp/wim_net_seg)
	    wim_uuid=$(uuidgen)
            docker exec -t son-postgres psql -h localhost -U postgres -d wimregistry -c "INSERT INTO WIM (UUID, TYPE, VENDOR, ENDPOINT, USERNAME, PASS, AUTHKEY) VALUES ('$wim_uuid', 'WIM', 'VTN', '$wim_ip', '$wim_user', '$wim_passwd', null);" > /dev/null
            docker exec -t son-postgres psql -h localhost -U postgres -d wimregistry -c "INSERT INTO SERVICED_SEGMENTS (NETWORK_SEGMENT, WIM_UUID) VALUES ('$wim_net_seg', '$wim_uuid');" > /dev/null
	    dialog --title "WIM Configuration" --msgbox "WIM was added" 6 50
            ;;
        5)
	    dialog --title "VIM Configuration" --no-cancel --inputbox "Please enter the VIM compute uuid to be deleted.\nExample: cbc5a4fa-59ed-4ec1-ad2d-adb270e21693" 10 60 2> /tmp/vim_uuid_delete
            vim_uuid_delete=$(cat /tmp/vim_uuid_delete)
	    docker exec -t son-postgres psql -h localhost -U postgres -d vimregistry -c "DELETE FROM VIM where uuid IN (SELECT NETWORKING_UUID FROM LINK_VIM where COMPUTE_UUID = '$vim_uuid_delete');" > /dev/null
	    docker exec -t son-postgres psql -h localhost -U postgres -d vimregistry -c "DELETE FROM VIM where uuid = '$vim_uuid_delete';" > /dev/null
	    dialog --title "VIM Configuration" --msgbox "VIM was deleted" 6 50
            ;;
        6)
	    dialog --title "WIM Configuration" --no-cancel --inputbox "Please enter the WIM uuid to be deleted.\nExample: cbc5a4fa-59ed-4ec1-ad2d-adb270e21693" 10 60 2> /tmp/wim_uuid_delete
            wim_uuid_delete=$(cat /tmp/wim_uuid_delete)
	    docker exec -t son-postgres psql -h localhost -U postgres -d wimregistry -c "DELETE FROM SERVICED_SEGMENTS where WIM_UUID = '$wim_uuid_delete';" > /dev/null
	    docker exec -t son-postgres psql -h localhost -U postgres -d wimregistry -c "DELETE FROM WIM where uuid = '$wim_uuid_delete';" > /dev/null
	    dialog --title "WIM Configuration" --msgbox "WIM was deleted" 6 50
            ;;
        7)
            echo "SONATA-NFV bye"; break ;;

esac

done
