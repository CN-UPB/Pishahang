package sonata.kernel.vimadaptor.wrapper.terraform;

import com.mitchellbosecke.pebble.PebbleEngine;
import com.mitchellbosecke.pebble.error.PebbleException;
import com.mitchellbosecke.pebble.template.PebbleTemplate;

import java.io.IOException;
import java.io.StringWriter;
import java.io.Writer;
import java.util.Map;

abstract public class TerraformTemplate {

    private String mainContent;

    private String serviceContent;

    /**
     * Get the content of the main terraform template.
     * @return String
     */
    public String getMainContent() throws IOException, PebbleException {
        if (this.mainContent == null && this.getMainTemplate() != null) {
            return this.mainContent = this.buildContent(this.getMainTemplate());
        }

        return this.mainContent;
    }

    /**
     * Get the content of the template.
     *
     * @return String
     */
    public String getServiceContent() throws IOException, PebbleException {
        if (this.serviceContent == null) {
            return this.serviceContent = this.buildContent(this.getServiceTemplate());
        }

        return this.serviceContent;
    }

    /**
     * Build the content of the template.
     *
     * @return String
     */
    public TerraformTemplate build() throws IOException, PebbleException {
        this.serviceContent = this.buildContent(this.getServiceTemplate());
        this.mainContent = this.buildContent(this.getMainTemplate());

        return this;
    }

    /**
     * Get the path to the main template file.
     *
     * @return String|null
     */
    public String getMainTemplate() {
        return null;
    }

    /**
     * Get the path to the service template file.
     *
     * @return String
     */
    abstract public String getServiceTemplate();

    abstract public Map<String, Object> getContext();

    /**
     * Build the template.
     */
    private String buildContent(String template) throws IOException, PebbleException {
        PebbleEngine engine = new PebbleEngine.Builder().build();
        PebbleTemplate compiledTemplate = engine.getTemplate(template);

        Writer writer = new StringWriter();
        Map<String, Object> context = this.getContext();

        compiledTemplate.evaluate(writer, context);

        return writer.toString();
    }
}
