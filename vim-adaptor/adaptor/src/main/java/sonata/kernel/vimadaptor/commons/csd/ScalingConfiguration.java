package sonata.kernel.vimadaptor.commons.csd;

public class ScalingConfiguration {
    private int minimum;

    private int maximum;

    public int getMinimum() {
        return minimum > 0 ? minimum : 1;
    }

    public void setMinimum(int minimum) {
        this.minimum = minimum;
    }

    public int getMaximum() {
        return maximum > 0 ? maximum : 1;
    }

    public void setMaximum(int maximum) {
        this.maximum = maximum;
    }
}
