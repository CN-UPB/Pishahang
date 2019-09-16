sudo apt-get install -y software-properties-common
sudo apt-add-repository -y ppa:ansible/ansible
sudo apt-get update
sudo apt-get install -y ansible
sudo apt-get install -y git
git clone --single-branch --branch mv-plugin https://github.com/CN-UPB/Pishahang.git

cd Pishahang/son-install

mkdir ~/.ssh
echo sonata | tee ~/.ssh/.vault_pass

ansible-playbook utils/deploy/sp.yml -e "target=localhost public_ip=$1" -v