# Commons 
Commons contains files, like definitions.*, that can be re-used by other schema definitions.

### Usage
To use the commons files, you might want to reference them in the following way:

```
$ref: "URI#/parameter"
```

For example:

```
$ref: "https://raw.githubusercontent.com/sonata-nfv/son-schema/master/commons/definitions.json#/images_formats" 
```

### Known issues
By default, the referencens only work, if you have an Internet connection and can access Github. Since references use URIs to address the corresponding file, you may use "file://..." as a protocol and reference to a local file. However, "file://..." requires an absolute path to the file, which is why we cannot have a generic solution that serves all.

Unfortunately, some JSON validators can not handle YAML references. Thus, we have to reference JSON files only, which is why the repository contains corresponding *.json files for all the *.yml files.

### References

 - [Structuring a complex schema](http://spacetelescope.github.io/understanding-json-schema/structuring.html)
