A set of useful roles:
* NTP
* Apache
* NGINX
* OTRS 5
* Jenkins (CI engine)
* KeyCloak (IdMgmt)
* Odoo (OpenERP Community Edition)

===
How to invoke:
# NTP
$ ansible-playbook utils/deploy-ntp.yml -e "target=localhost"
# Apache
$ ansible-playbook utils/deploy-apache.yml -e "target=localhost"
# NGINX
$ ansible-playbook utils/deploy-nginx.yml -e "target=localhost"
# OTRS
$ ansible-playbook utils/deploy-otrs.yml -e "target=localhost"
# Jenkins
$ ansible-playbook utils/deploy-jenkins.yml -e "target=localhost"
# Keycloak
$ ansible-playbook utils/deploy-keycloak.yml -e "target=localhost"
# Odoo
$ ansible-playbook utils/deploy-odoo.yml -e "target=localhost"

===
Report feedback to: 
'Alberto Rocha <arocha@ptinovacao.pt>'
