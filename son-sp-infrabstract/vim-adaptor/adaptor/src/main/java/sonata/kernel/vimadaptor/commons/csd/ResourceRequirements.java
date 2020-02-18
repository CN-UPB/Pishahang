package sonata.kernel.vimadaptor.commons.csd;

import com.fasterxml.jackson.annotation.JsonProperty;

public class ResourceRequirements {

    @JsonProperty("cpu")
    private CpuRequirements cpu;

    @JsonProperty("memory")
    private MemoryRequirements memory;

    @JsonProperty("gpu")
    private GpuRequirements gpu;

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

    public GpuRequirements getGpu() {
        return gpu;
    }

    public void setGpu(GpuRequirements gpu) {
        this.gpu = gpu;
    }


}
