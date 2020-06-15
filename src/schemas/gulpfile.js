var Ajv = require("ajv");
const del = require("del");
const gulp = require("gulp");
const path = require("path");
const RefParser = require("@apidevtools/json-schema-ref-parser");
const { Readable } = require("stream");
const through = require("through2");
const yaml = require("js-yaml");
const mergeAllOf = require("json-schema-merge-allof");

const { promisify } = require("util");
const pipeline = promisify(require("stream").pipeline);

const IN_DIR = "lib";
const OUT_DIR = "bundled";

// Utilities

/**
 * Given an async function, returns a streams.Transform object that runs the async
 * function, passing in `chunk`.
 */
function makeStreamTransformer(transformerFunction) {
  return through.obj(function (chunk, encoding, callback) {
    transformerFunction
      .bind(this)(chunk)
      .then(
        () => callback(),
        (error) => callback(error)
      );
  });
}

async function getBundledSchema(filePath) {
  return mergeAllOf(await RefParser.dereference(filePath));
}

function getRelativePath(filePath) {
  return path.relative(process.cwd(), filePath);
}

// Gulp Tasks

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
    makeStreamTransformer(async function (file) {
      let schema = await RefParser.dereference(file.path);
      schema = mergeAllOf(schema);

      const yamlFile = file.clone();
      yamlFile.contents = Readable.from([yaml.dump(schema)]);
      this.push(yamlFile);

      const jsonFile = file.clone();
      jsonFile.extname = ".json";
      jsonFile.contents = Readable.from([JSON.stringify(schema, null, 2)]);
      this.push(jsonFile);
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
  const schemaCache = {};

  return pipeline(
    gulp.src(IN_DIR + "/**/*-tests/*.yml"),
    makeStreamTransformer(async function (file) {
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

      if (typeof schemaCache[schemaPath] === "undefined") {
        schemaCache[schemaPath] = await getBundledSchema(schemaPath);
      }
      const schema = schemaCache[schemaPath];

      const data = yaml.safeLoad(file.contents);
      const validate = ajv.compile(schema);
      const valid = validate(data);
      if (shouldDataBeValid && !valid) {
        console.log(validate.errors);
        throw validate.errors[0];
      }
      if (!shouldDataBeValid && valid) {
        throw new Error(
          `${relativeFilePath} is valid against ${relativeSchemaPath} although it is suffixed with ".invalid.yml"`
        );
      }
    })
  );
}

exports.test = testSchemas;
