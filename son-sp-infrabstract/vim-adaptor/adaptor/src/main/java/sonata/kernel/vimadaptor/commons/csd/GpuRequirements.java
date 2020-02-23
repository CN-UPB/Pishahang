package sonata.kernel.vimadaptor.commons.csd;

import com.fasterxml.jackson.annotation.JsonProperty;

public class GpuRequirements {

    @JsonProperty("gpus")
    private int Gpus;

    @JsonProperty("type")
    private String gType;

    public int getGpus() {
        return Gpus;
    }

    public void setGpus(int Gpus) {
        this.Gpus = Gpus;
    }

    public String getGpuType() {
        return gType;
    }

    public void setGpuType(String gType) {
        this.gType = gType;
    }
}
