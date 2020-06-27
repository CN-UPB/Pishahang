{% for vdu in descriptor.virtual_deployment_units %}
resource "kubernetes_deployment" "{{ vdu.id }}-{{ function_instance_id }}" {
  metadata {
    name = "{{ vdu.id }}-{{ function_instance_id }}"
    labels = {
      service = "{{ service_instance_id  }}"
      function = "{{ function_instance_id }}"
      vdu = "{{ vdu.id }}"
    }
  }

  spec {
    selector {
      match_labels = {
        service = "{{ service_instance_id  }}"
        function = "{{ function_instance_id }}"
        vdu = "{{ vdu.id }}"
      }
    }

    template {
      metadata {
        labels = {
          service = "{{ service_instance_id  }}"
          function = "{{ function_instance_id }}"
          vdu = "{{ vdu.id }}"
        }
      }

      spec {
        container {
          image = "{{ vdu.service_image }}"
          name  = "{{ vdu.id }}-{{ service_instance_id  }}"

          {% for port in vdu.service_ports %}
            port {
              {% if port.name != null %}
              name = "{{ port.name }}"
              {% endif %}
              {% if port.protocol != null %}
              protocol = "{{ port.protocol }}"
              {% endif %}
              container_port = {{ port.target_port }}
            }
          {% endfor %}

          {% if vdu.resource_requirements != null %}
            resources {
              requests {
                {% if vdu.resource_requirements.cpu != null %}
                  cpu = {{ vdu.resource_requirements.cpu.vcpus }}
                {% endif %}
                {% if vdu.resource_requirements.memory != null %}
                  memory = "{{ vdu.resource_requirements.memory.size }}{{ vdu.resource_requirements.memory.size_unit }}"
                {% endif %}
              }

              limits {
                {% if vdu.resource_requirements.cpu != null %}
                  cpu = {{ vdu.resource_requirements.cpu.vcpus }}
                {% endif %}
                {% if vdu.resource_requirements.memory != null %}
                  memory = "{{ vdu.resource_requirements.memory.size }}{{ vdu.resource_requirements.memory.size_unit }}"
                {% endif %}
              }
            }
          {% endif %}

          {% if vdu.environment_variables != null %}
            {% for env in vdu.environment_variables %}
              env {
                name = "{{ env.name }}"
                value = "{{ env.value }}"
              }
            {% endfor %}
          {% endif %}
        }
      }

    }
  }
}

resource "kubernetes_service" "{{ vdu.id }}-{{ function_instance_id }}" {
  metadata {
    {% if vdu.name != null %}
      name = "{{ vdu.name }}"
    {% else %}
      name = "{{ vdu.id }}-{{ function_instance_id }}"
    {% endif %}

    labels = {
      service = "{{ service_instance_id  }}"
      function = "{{ function_instance_id }}"
      vdu = "{{ vdu.id }}"
    }
  }

  spec {
    selector = {
      service = "{{ service_instance_id  }}"
      function = "{{ function_instance_id }}"
      vdu = "{{ vdu.id }}"
    }

    type = "{{ vdu.service_type }}"

    {% for port in vdu.service_ports %}
      port {
        {% if port.name != null %}
          name = "{{ port.name }}"
        {% endif %}
        {% if port.protocol != null %}
          protocol = "{{ port.protocol }}"
        {% endif %}
        port = {{ port.port }}
        target_port = {{ port.target_port }}
      }
    {% endfor %}
  }
}

{% if vdu.scale_in_out != null %}
resource "kubernetes_horizontal_pod_autoscaler" "{{ vdu.id }}-{{ function_instance_id }}" {
  metadata {
    name = "{{ vdu.id }}-{{ function_instance_id }}"
  }
  
  spec {
    max_replicas = {{ vdu.scale_in_out.maximum }}
    min_replicas = {{ vdu.scale_in_out.minimum }}
    scale_target_ref {
      api_version = "apps/v1"
      kind = "Deployment"
      name = "{{ vdu.id }}-{{ function_instance_id }}"
    }
  }
}
{% endif %}

{% endfor %}