{% for vdu in descriptor.virtual_deployment_units %}
  resource "aws_instance" "{{vdu.id}}" {
    ami           = "{{vdu.ami}}"
    instance_type = "{{vdu.instance_type}}"

    tags = {
      Name = "{{vdu.name}}-{{function_instance_id}}"
      
      service_instance = "{{service_instance_id}}"
      function_instance = "{{function_instance_id}}"
      vdu_id = "{{vdu.id}}"
      vdu_name = "{{vdu.name}}"
    }
  }
{% endfor %}
