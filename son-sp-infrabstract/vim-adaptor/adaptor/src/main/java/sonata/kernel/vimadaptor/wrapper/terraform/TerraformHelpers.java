package sonata.kernel.vimadaptor.wrapper.terraform;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;

public class TerraformHelpers {
    /**
     * Transformer an object to YAML.
     *
     * @param data Object
     *
     * @return String
     */
    public static String transformToYAML(Object data) throws JsonProcessingException {
        return getObjectMapper().writeValueAsString(data);
    }

    /**
     * Get the object mapper which transforms object to YAML.
     *
     * @return ObjectMapper
     */
    private static ObjectMapper getObjectMapper() {
        ObjectMapper mapper = new ObjectMapper(new YAMLFactory());
        mapper.disable(SerializationFeature.WRITE_EMPTY_JSON_ARRAYS);
        mapper.enable(SerializationFeature.WRITE_ENUMS_USING_TO_STRING);
        mapper.disable(SerializationFeature.WRITE_NULL_MAP_VALUES);
        mapper.setSerializationInclusion(JsonInclude.Include.NON_NULL);

        return mapper;
    }
}
