import yaml from "js-yaml";

/**
 * Converts arbitrary json data to a yaml string
 *
 * @param jsonData The object to be converted
 */
export function convertJsonToYaml(jsonData: any) {
  try {
    // Get document, or throw exception on error
    return yaml.safeDump(jsonData);
  } catch (e) {
    console.log("E: " + e);
  }
}
