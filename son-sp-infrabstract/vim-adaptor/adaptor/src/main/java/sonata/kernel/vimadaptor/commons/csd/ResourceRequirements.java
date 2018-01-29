package sonata.kernel.vimadaptor.commons.csd;

import com.fasterxml.jackson.annotation.JsonProperty;

public class ResourceRequirements {

    @JsonProperty("cpu")
    private CpuRequirements cpu;

    @JsonProperty("memory")
    private MemoryRequirements memory;

    public CpuRequirements getCpu() {
        return cpu;
    }

    public void setCpu(CpuRequirements cpu) {
        this.cpu = cpu;
    }

    public MemoryRequirements getMemory() {
        return memory;
    }

    public void setMemory(MemoryRequirements memory) {
        this.memory = memory;
    }
}
