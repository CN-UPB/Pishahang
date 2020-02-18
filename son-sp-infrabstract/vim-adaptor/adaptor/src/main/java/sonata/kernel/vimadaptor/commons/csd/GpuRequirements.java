package sonata.kernel.vimadaptor.commons.csd;

import com.fasterxml.jackson.annotation.JsonProperty;

public class GpuRequirements {

    @JsonProperty("gpus")
    private int Gpus;

    public int getGpus() {
        return Gpus;
    }

    public void setGpus(int Gpus) {
        this.Gpus = Gpus;
    }
}
