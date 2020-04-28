package sonata.kernel.vimadaptor.commons.csd;

import com.fasterxml.jackson.annotation.JsonProperty;

public class ResourceUtilisation {

    @JsonProperty("CPU_total")
    public int totCores;
    @JsonProperty("memory_total")
    public int totMemory;
    @JsonProperty("CPU_used")
    public int usedCores;
    @JsonProperty("memory_used")
    public int usedMemory;

    public ResourceUtilisation() {
        this.totCores = 0;
        this.totMemory = 0;
        this.usedCores = 0;
        this.usedMemory = 0;
    }

    public ResourceUtilisation(int totCores, int totMemory, int usedCores, int usedMemory) {
        this.totCores = totCores;
        this.totMemory = totMemory;
        this.usedCores = usedCores;
        this.usedMemory = usedMemory;
    }

    public int getTotCores() {
        return totCores;
    }

    public int getTotMemory() {
        return totMemory;
    }

    public int getUsedCores() {
        return usedCores;
    }

    public int getUsedMemory() {
        return usedMemory;
    }

    public void setTotCores(int totCores) {
        this.totCores = totCores;
    }

    public void setTotMemory(int totMemory) {
        this.totMemory = totMemory;
    }

    public void setUsedCores(int usedCores) {
        this.usedCores = usedCores;
    }

    public void setUsedMemory(int usedMemory) {
        this.usedMemory = usedMemory;
    }

    @Override
    public String toString() {
        String out = "totMem: " + totMemory + "/usedMem: " + usedMemory + "\n";
        out += "totCore: " + totCores + "/usedMem: " + usedCores;
        return out;
    }
}
