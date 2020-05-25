{% for vdu in descriptor.virtual_deployment_units %}
resource "kubernetes_replication_controller" "{{ vdu.id }}-{{ vdu.instance_uuid }}" {
  metadata {
    name = "{{ vdu.id }}-{{ vdu.instance_uuid }}"
    labels {
      service = "{{ service_instance_id  }}"
      vdu = "{{ vdu.id }}"
    }
  }

  spec {
    selector {
      service = "{{ service_instance_id  }}"
      vdu = "{{ vdu.id }}"
    }
    template {
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
                    cpu = {{ vdu.resource_requirements.cpu.v_cpus }}
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

resource "kubernetes_service" "{{ vdu.id }}-{{ vdu.instance_uuid }}" {
  metadata {
    {% if vdu.name != null %}
      name = "{{ vdu.name }}"
    {% else %}
      name = "{{ vdu.id }}-{{ vdu.instance_uuid }}"
    {% endif %}

    labels {
      service = "{{ service_instance_id  }}"
      vdu = "{{ vdu.id }}"
    }
  }
  spec {
    selector {
      vdu = "${kubernetes_replication_controller.{{ vdu.id }}-{{ vdu.instance_uuid }}.metadata.0.labels.vdu}"
    }

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

    type = "{{ vdu.service_type }}"
  }
}

    {% if vdu.scale_in_out != null %}
        resource "kubernetes_horizontal_pod_autoscaler" "{{ vdu.id }}-{{ vdu.instance_uuid }}" {
          metadata {
              name = "{{ vdu.id }}-{{ vdu.instance_uuid }}"

              labels {
              service = "{{ service_instance_id  }}"
              vdu = "{{ vdu.id }}"
              }
          }
          spec {
              max_replicas = {{ vdu.scale_in_out.maximum }}
              min_replicas = {{ vdu.scale_in_out.minimum }}
              scale_target_ref {
              kind = "ReplicationController"
              name = "${kubernetes_replication_controller.{{ vdu.id }}-{{ vdu.instance_uuid }}.metadata.0.name}"
              }
          }
        }
    {% endif %}
{% endfor %}