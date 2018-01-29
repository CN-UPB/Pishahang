<?php
$vars = array();
$debug=false;
/*
$vars['MON_URL']=($debug==true?'http://192.168.1.127:8000':getenv('MON_URL'));
$vars['GK_URL']=($debug==true?'https://sp.int3.sonata-nfv.eu/api/v2':getenv('GK_URL'));
$vars['LOGS_URL']=($debug==true?'http://logs.sonata-nfv.eu:12900':getenv('LOGS_URL'));
$vars['VIMS_URL']=($debug==true?'https://sp.int3.sonata-nfv.eu/api/v2':getenv('GK_URL'));
*/
$vars['MON_URL']=($debug==true?'http://192.168.1.127:8000':url() . '/monitoring');
$vars['GK_URL']=($debug==true?'https://sp.int3.sonata-nfv.eu/api/v2':url() . '/api/v2');
$vars['LOGS_URL']=($debug==true?'http://logs.sonata-nfv.eu:12900':url()) . '/logs';
$vars['VIMS_URL']=($debug==true?'https://sp.int3.sonata-nfv.eu/api/v2':url() . '/api/v2');
echo json_encode($vars);
function url(){
  return sprintf(
    "%s://%s",
    isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] != 'off' ? 'https' : 'http',    $_SERVER['SERVER_NAME'] );
}
?>