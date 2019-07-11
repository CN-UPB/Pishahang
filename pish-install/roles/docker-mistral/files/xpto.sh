python -c "
  import ConfigParser
  c = ConfigParser.ConfigParser()
  c.read('/home/mistral/mistral.conf')
  c.set('DEFAULT', 'transport_url', 'rabbit://guest:guest@rabbitmq:5672/')
  c.set('database','connection','mysql://root:strangehat@mysql:3306/mistral')
  c.set('pecan', 'auth_enable', 'false')
  with open('/home/mistral/mistral.conf', 'w') as f:
  c.write(f)
"
