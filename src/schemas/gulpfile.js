var Ajv = require("ajv");
const del = require("del");
const gulp = require("gulp");
const path = require("path");
const RefParser = require("@apidevtools/json-schema-ref-parser");
const { Readable } = require("stream");
const through = require("through2");
const yaml = require("js-yaml");

const { promisify } = require("util");
const pipeline = promisify(require("stream").pipeline);

const IN_DIR = "lib";
const OUT_DIR = "bundled";

function clean() {
  return del(OUT_DIR);
}

/**
 * Resolve references in all YAML files from IN_DIR and store the resulting bundled
 * schema files in OUT_DIR as JSON and YAML.
 */
function compile() {
  return pipeline(
    gulp.src([IN_DIR + "/**/*.yml", "!**/*-tests/**/*"]),
    through.obj(function (file, encoding, callback) {
      RefParser.bundle(file.path, (err, schema) => {
        if (err) {
          callback(err);
        } else {
          const yamlFile = file.clone();
          yamlFile.contents = Readable.from([yaml.dump(schema)]);
          this.push(yamlFile);

          const jsonFile = file.clone();
          jsonFile.extname = ".json";
          jsonFile.contents = Readable.from([JSON.stringify(schema, null, 2)]);
          this.push(jsonFile);

          callback();
        }
      });
    }),
    gulp.dest(OUT_DIR)
  );
}

exports.bundle = gulp.series(clean, compile);

/**
 * For each yaml file that ends in `.yml` or `.invalid.yml` and is located in a
 * `*-tests` directory that has a *.yml schema file next to it, runs `ajv` to validate
 * the file's contents against the given schema. Validation failures will fail the task
 * when the corresponding data file ends in a plain `.yml` and, vice versa, successful
 * validation will fail the task when the corresponding data file ends in `.invalid.yml`.
 */
function testSchemas() {
  const ajv = new Ajv();

  const getRelativePath = (filePath) => path.relative(process.cwd(), filePath);

  return pipeline(
    gulp.src(IN_DIR + "/**/*-tests/*.yml"),
    through.obj(function (file, encoding, callback) {
      const testDir = path.dirname(file.path);
      const schemaFileName = path.basename(testDir).replace("-tests", "");
      const schemaPath = path.join(
        path.dirname(testDir),
        schemaFileName + ".yml"
      );
      const shouldDataBeValid = !path
        .basename(file.path)
        .endsWith(".invalid.yml");

      // Relative paths for logging
      const relativeFilePath = getRelativePath(file.path);
      const relativeSchemaPath = getRelativePath(schemaPath);

      console.log(
        `Validating ${relativeFilePath} against ${relativeSchemaPath}`
      );

      RefParser.bundle(schemaPath, (err, schema) => {
        if (err) {
          callback(err);
        } else {
          const data = yaml.safeLoad(file.contents);
          const validate = ajv.compile(schema);
          const valid = validate(data);
          if (shouldDataBeValid)
            if (!valid) {
              console.log(validate.errors);
              callback(validate.errors[0]);
            } else {
              callback();
            }
          else {
            if (valid) {
              callback(
                new Error(
                  `${relativeFilePath} is valid against ${relativeSchemaPath} although it is suffixed with ".invalid.yml"`
                )
              );
            } else {
              callback();
            }
          }
        }
      });
    })
  );
}

exports.test = testSchemas;
