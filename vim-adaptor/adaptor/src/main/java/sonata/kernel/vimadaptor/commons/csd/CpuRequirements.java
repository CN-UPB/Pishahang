package sonata.kernel.vimadaptor.commons.csd;

import com.fasterxml.jackson.annotation.JsonProperty;

public class CpuRequirements {

    @JsonProperty("vcpus")
    private float vCpus;

    public float getvCpus() {
        return vCpus;
    }

    public void setvCpus(float vCpus) {
        this.vCpus = vCpus;
    }
}
